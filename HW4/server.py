import grpc
from concurrent import futures
import time
import chat_pb2
import chat_pb2_grpc
from storage import Storage
import queue
import os
import sys
import socket
import threading

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, port, is_leader=False, leader_address=None, replica_addresses=None):
        self.port = port
        self.ip = get_local_ip()
        self.is_leader = is_leader
        self.leader_address = leader_address
        self.storage = Storage(f"chat-{port}.db")
        self.online_users = {}

        self.replica_addresses = replica_addresses if replica_addresses else []
        self.replicas = []

        if self.is_leader:
            self.replicas = [
                chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(addr))
                for addr in self.replica_addresses
            ]
        else:
            self.leader_channel = grpc.insecure_channel(self.leader_address)
            self.leader_stub = chat_pb2_grpc.ChatServiceStub(self.leader_channel)
            self.FollowerSync()
            threading.Thread(target=self.Monitor, daemon=True).start()

    def Login(self, request, context):
        response = self.storage.login_register_user(request.username, request.password)
        if response["status"] == "success":
            self.online_users[request.username] = queue.Queue()
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def Logout(self, request, context):
        self.online_users.pop(request.username, None)
        return chat_pb2.Response(status="success", message="User logged out.")

    def SendMessage(self, request, context):
        if not self.is_leader:
            return chat_pb2.Response(status="error", message="Not the leader")

        sender = request.username
        recipient = request.recipient
        message = request.message
        message_id = int(time.time())

        self.storage.send_message(sender, recipient, message, status='read')
        self.Broadcast_Sync()

        return chat_pb2.Response(status="success", message="Message sent")

    def Broadcast_Sync(self):
        for replica in self.replicas:
            try:
                replica.FollowerSync()
            except grpc.RpcError as e:
                print(f"Error syncing data to replica: {e}")

    def SyncData(self, request, context):
        if not self.is_leader:
            return chat_pb2.SyncDataResponse(status="error")

        replica_address = request.replica_address
        if replica_address not in self.replica_addresses:
            print(f"New replica found: {replica_address}")
            self.replica_addresses.append(replica_address)
            self.replicas.append(chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(replica_address)))

        all_messages = self.storage.get_all_messages()
        all_users = self.storage.get_all_users()

        message_data = [chat_pb2.MessageData(**msg) for msg in all_messages]
        user_data = [chat_pb2.UserData(username=user['username'], password_hash=user['password_hash']) for user in all_users]

        tmp_replica_addresses = self.replica_addresses.copy()
        if replica_address in tmp_replica_addresses:
            tmp_replica_addresses.remove(replica_address)

        print(f"Syncing data to replica: {replica_address}")
        return chat_pb2.SyncDataResponse(
            status="success",
            replica_addresses=tmp_replica_addresses,
            messages=message_data,
            users=user_data
        )

    def FollowerSync(self, request=None, context=None):
        if request is not None:
            self.leader_address = request.leader_address
            self.leader_channel = grpc.insecure_channel(self.leader_address)
            self.leader_stub = chat_pb2_grpc.ChatServiceStub(self.leader_channel)

        sync_request = chat_pb2.SyncDataRequest(replica_address=f"{self.ip}:{self.port}")
        response = self.leader_stub.SyncData(sync_request)

        if response.status == "success":
            self.storage.store_synced_data(response.messages, response.users)
            for replica_address in response.replica_addresses:
                if replica_address not in self.replica_addresses:
                    self.replica_addresses.append(replica_address)
                    self.replicas.append(chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(replica_address)))
        print(f"Synced with leader on port {self.leader_address.split(':')[-1]}")
        return chat_pb2.Response(status=response.status, message="Synced")

    def Monitor(self):
        hb_request = chat_pb2.HeartbeatRequest()
        while not self.is_leader:
            try:
                self.leader_stub.Heartbeat(hb_request)
            except grpc.RpcError:
                print("Leader is down. Starting election...")
                self.initiate_election()
            time.sleep(1)

    def initiate_election(self):
        higher_nodes = [addr for addr in self.replica_addresses if int(addr.split(":")[-1]) > self.port]
        got_response = False
        for addr in higher_nodes:
            try:
                stub = chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(addr))
                req = chat_pb2.ElectionRequest(candidate_address=f"{self.ip}:{self.port}", candidate_port=self.port)
                stub.StartElection(req)
                got_response = True
                break
            except grpc.RpcError:
                continue
        if not got_response:
            self.AnnounceNewLeader()

    def AnnounceNewLeader(self):
        self.is_leader = True
        print(f"I am the new leader on port {self.port}")
        for addr in self.replica_addresses:
            try:
                stub = chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(addr))
                stub.AnnounceLeader(chat_pb2.CoordinatorMessage(new_leader_address=f"{self.ip}:{self.port}"))
            except grpc.RpcError:
                continue

    def StartElection(self, request, context):
        print(f"Election request received from {request.candidate_address}.")
        return chat_pb2.ElectionResponse(status="OK")

    def AnnounceLeader(self, request, context):
        print(f"New leader announced: {request.new_leader_address}")
        self.leader_address = request.new_leader_address
        self.leader_channel = grpc.insecure_channel(self.leader_address)
        self.leader_stub = chat_pb2_grpc.ChatServiceStub(self.leader_channel)
        self.is_leader = False
        return chat_pb2.Response(status="success", message="Leader updated.")

    def Heartbeat(self, request, context):
        return chat_pb2.Response(status="alive", message="Heartbeat acknowledged")

    def ListAccounts(self, request, context):
        return chat_pb2.ListAccountsResponse(
            status="success",
            usernames=self.storage.list_accounts(page_num=request.page_num).get("usernames", [])
        )

    def ReadMessages(self, request, context):
        limit = max(0, min(request.limit, 10))
        if limit == 0:
            return chat_pb2.ReadMessagesResponse(status="success", messages=[])

        messages = self.storage.read_messages(request.username, limit)
        return chat_pb2.ReadMessagesResponse(
            status=messages["status"],
            messages=[chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"]) for msg in messages.get("messages", [])]
        )

    def ListenForMessages(self, request, context):
        if request.username not in self.online_users:
            context.abort(grpc.StatusCode.NOT_FOUND, "User not logged in")
        q = self.online_users[request.username]
        while True:
            try:
                message = q.get(timeout=10)
                yield message
            except queue.Empty:
                continue
            except grpc.RpcError:
                self.online_users.pop(request.username, None)
                break

    def DeleteMessage(self, request, context):
        response = self.storage.delete_message(request.username, request.recipient)
        if self.is_leader:
            self.Broadcast_Sync()
        return chat_pb2.Response(status=response["status"], message=response["message"])

    def DeleteAccount(self, request, context):
        response = self.storage.delete_account(request.username, request.password)
        if response["status"] == "success":
            self.online_users.pop(request.username, None)
        if self.is_leader:
            self.Broadcast_Sync()
        return chat_pb2.Response(status=response["status"], message=response["message"])

def serve(is_leader=False, leader_address=None, replica_addresses=None, port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_service = ChatService(
        port=port,
        is_leader=is_leader,
        leader_address=leader_address,
        replica_addresses=replica_addresses
    )
    chat_pb2_grpc.add_ChatServiceServicer_to_server(chat_service, server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    print(f"Starting {'leader' if is_leader else 'follower'} server on port {port}...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--leader', action='store_true', help="Run this server as a leader")
    parser.add_argument('--port', type=int, default=50051)
    parser.add_argument('--replicas', nargs='*', default=[])
    parser.add_argument('--leader_address', type=str, default='0.0.0.0:50051')
    args = parser.parse_args()

    serve(
        is_leader=args.leader,
        leader_address=args.leader_address,
        replica_addresses=args.replicas,
        port=args.port
    )