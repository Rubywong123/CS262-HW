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

def get_local_ip():
    # This opens a dummy connection to a public IP to get the right interface/IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable, just forces IP resolution
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

class LeaderChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, port, replica_addresses=None):
        self.port = port
        self.ip = get_local_ip()
        self.storage = Storage(f"chat-{port}.db")
        self.online_users = {}  # username -> queue of messages

        self.replica_addresses = replica_addresses if replica_addresses else []
        self.replicas = [
            chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(addr))
            for addr in replica_addresses
        ] if replica_addresses else []

    # Handle login request
    def Login(self, request, context):
        response = self.storage.login_register_user(request.username, request.password)
        if response["status"] == "success":
            self.online_users[request.username] = queue.Queue()
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    # Handle logout request
    def Logout(self, request, context):
        self.online_users.pop(request.username, None)
        return chat_pb2.Response(status="success", message="User logged out.")

    # Send message logic for the leader
    def SendMessage(self, request, context):
        sender = request.username
        recipient = request.recipient
        message = request.message
        message_id = int(time.time())

        chat_msg = chat_pb2.Message(id=message_id, sender=sender, message=message)
        self.storage.send_message(sender, recipient, message, status='read')

        self.Broadcast_Sync()

    def Broadcast_Sync(self):
        # Tell the followers to sync the data
        for replica in self.replicas:
            try:
                replica.FollowerSync()
            except grpc.RpcError as e:
                print(f"Error syncing data to replica: {e}")
                continue

    # Handle data sync request from followers
    def SyncData(self, request, context):
        """
        This method is responsible for syncing data from the leader to the follower.
        It will return the current data (messages, accounts) to the follower.
        """
        # check if the follower is already in the list of replicas
        # if not, add it to the list

        replica_address = request.replica_address

        if replica_address not in self.replica_addresses:
            self.replica_addresses.append(replica_address)
            self.replicas.append(chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(replica_address)))

        # get all the data points from the database
        all_messages = self.storage.get_all_messages()
        all_users = self.storage.get_all_users()

        all_messages = [chat_pb2.MessageData(id=msg['id'], sender=msg['sender'], recipient=msg['recipient'], message=msg['message'], status = msg['status']) for msg in all_messages]
        all_users = [chat_pb2.UserData(username=user['username'], password_hash=user['password_hash']) for user in all_users]

        tmp_replica_addresses = self.replica_addresses.copy()
        tmp_replica_addresses.remove(replica_address)
        return chat_pb2.SyncDataResponse(
            status="success",
            replica_addresses=tmp_replica_addresses,
            messages=all_messages,
            users=all_users
        )

    def ListAccounts(self, request, context):
        # distribute the request to the followers
        if self.replicas:
            for replica in self.replicas:
                try:
                    response = replica.ListAccounts(request)
                    print(f"Replica response: {response}")
                    break
                except grpc.RpcError as e:
                    print(f"Error getting list of accounts from replica: {e}")
                    continue
            return response
        else:
            # do it locally
            response = self.storage.list_accounts(page_num=request.page_num)
            return chat_pb2.ListAccountsResponse(status=response["status"], usernames=response.get("usernames", []))

    def ReadMessages(self, request, context):
        if self.replicas:
            # distribute the request to the followers
            for replica in self.replicas:
                try:
                    response = replica.ReadMessages(request)
                    print(f"Replica response: {response}")
                    break
                except grpc.RpcError as e:
                    print(f"Error reading messages from replica: {e}")
                    continue
            return response
        else:
            # do it locally
            limit = max(0, min(request.limit, 10))
            if limit == 0:
                return chat_pb2.ReadMessagesResponse(status="success", messages=[])

            messages = self.storage.read_messages(request.username, limit)
            return chat_pb2.ReadMessagesResponse(
                status=messages["status"],
                messages=[
                    chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"])
                    for msg in messages.get("messages", [])
                ]
            )

    def ListenForMessages(self, request, context):
        username = request.username
        if username not in self.online_users:
            context.abort(grpc.StatusCode.NOT_FOUND, "User not logged in")

        q = self.online_users[username]
        while True:
            try:
                message = q.get(timeout=10)
                yield message
            except queue.Empty:
                continue
            except grpc.RpcError:
                self.online_users.pop(username, None)
                break

    def DeleteMessage(self, request, context):
        response = self.storage.delete_message(request.username, request.recipient)

        # Tell the followers to sync the data
        self.Broadcast_Sync()
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def DeleteAccount(self, request, context):
        response = self.storage.delete_account(request.username, request.password)
        if response["status"] == "success":
            self.online_users.pop(request.username, None)
        
        # Tell the followers to sync the data
        self.Broadcast_Sync()
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

class FollowerChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, port, leader_address):
        self.port = port
        self.ip = get_local_ip()
        self.storage = Storage(f"chat-{port}.db")
        self.online_users = {}  # username -> queue of messages
        self.leader_address = leader_address
        self.leader_channel = grpc.insecure_channel(leader_address)
        self.leader_stub = chat_pb2_grpc.ChatServiceStub(self.leader_channel)

        self.replica_addresses = []
        self.replicas = []

        # Connect to the leader by requesting the data
        self.FollowerSync()

        # monitor the leader and other replicas
        self.Monitor()
        
    # Follower only needs to request sync data from the leader
    def FollowerSync(self, request=None, context=None):
        """
        This method is called by a follower to request data from the leader.
        """
        if request is not None:
            print("New leader address received. We'll have to reconnect to the new leader.")
            self.leader_address = request.leader_address
            self.leader_channel = grpc.insecure_channel(self.leader_address)
            self.leader_stub = chat_pb2_grpc.ChatServiceStub(self.leader_channel)

        sync_request = chat_pb2.SyncDataRequest(f"{self.ip}:{self.port}")
        response = self.leader_stub.SyncData(sync_request)
        
        if response.status == "success":
            print(f"Follower: Data synced successfully from leader.")
            # Store the data (messages, users) locally in the follower's storage
            response = self.storage.store_synced_data(response.messages, response.users)

            # Connect to the other replicas
            for replica_address in response.replica_addresses:
                if replica_address != self.replica_address:
                    self.replica_addresses.append(replica_address)
                    self.replicas.append(chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(replica_address)))
        else:
            print(f"Follower: Failed to sync data from leader.")
        return chat_pb2.Response(status=response.status, message=response.message)

    def Monitor(self):
        # Do hearbeats check to the leader
        hb_request = chat_pb2.HeartbeatRequest()
        while True:
            try:
                response = self.leader_stub.Heartbeat(hb_request)
            except grpc.RpcError as e:

                # the leader is down, do the leader election
                print(f"Leader is down, starting leader election...")
                raise NotImplementedError("Leader election is not implemented yet.")

            # and other replicas
            for replica in self.replicas:
                try:
                    response = replica.Heartbeat(hb_request)
                except grpc.RpcError as e:
                    print(f"Replica is down: {e}")
                    raise NotImplementedError("Leader election is not implemented yet.")
            time.sleep(1)
    
    def ListAccounts(self, request, context):
        response = self.storage.list_accounts(page_num=request.page_num)
        return chat_pb2.ListAccountsResponse(status=response["status"], usernames=response.get("usernames", []))
    
    def ReadMessages(self, request, context):
        limit = max(0, min(request.limit, 10))
        if limit == 0:
            return chat_pb2.ReadMessagesResponse(status="success", messages=[])

        messages = self.storage.read_messages(request.username, limit)
        return chat_pb2.ReadMessagesResponse(
            status=messages["status"],
            messages=[
                chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"])
                for msg in messages.get("messages", [])
            ]
        )


def serve(is_leader=False, leader_address=None, replica_addresses=None, port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Serve as a leader or follower depending on the argument
    if is_leader:
        chat_pb2_grpc.add_ChatServiceServicer_to_server(LeaderChatService(replica_addresses), server)
    else:
        chat_pb2_grpc.add_ChatServiceServicer_to_server(FollowerChatService(leader_address), server)

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

    
    if args.leader:
        serve(is_leader=True, replica_addresses=args.replicas, port=args.port)
    else:
        if not args.leader_address:
            print("Error: A leader address must be provided for followers.")
            sys.exit(1)
        serve(is_leader=False, leader_address=args.leader_address, port=args.port)
