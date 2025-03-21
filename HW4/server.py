import grpc
from concurrent import futures
import time
import chat_pb2
import chat_pb2_grpc
from storage import Storage
import queue
from queue import Queue
import sys
import os

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, is_leader=False, replica_addresses=None):
        self.storage = Storage(f"data_{os.getenv('REPLICA_ID', '0')}.db")
        self.online_users = {}  # username -> queue of messages
        self.is_leader = is_leader

        if self.is_leader and replica_addresses:
            self.replicas = [
                chat_pb2_grpc.ChatServiceStub(grpc.insecure_channel(addr))
                for addr in replica_addresses
            ]
        else:
            self.replicas = []

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
            return chat_pb2.Response(status="error", message="This server is not the leader.")

        sender = request.username
        recipient = request.recipient
        message = request.message
        message_id = int(time.time())

        chat_msg = chat_pb2.Message(id=message_id, sender=sender, message=message)
        self.storage.send_message(sender, recipient, message, status='read')

        replicate_request = chat_pb2.ReplicateMessageRequest(message=chat_msg, recipient=recipient)

        ack_count = 1  # leader's own write
        for stub in self.replicas:
            try:
                response = stub.ReplicateMessage(replicate_request)
                if response.status == "success":
                    ack_count += 1
            except grpc.RpcError as e:
                print(f"[Replication error] {e}")

        if ack_count >= 2:
            return chat_pb2.Response(status="success", message="Message replicated successfully.")
        else:
            return chat_pb2.Response(status="error", message="Failed to replicate to quorum.")

    def ReplicateMessage(self, request, context):
        msg = request.message
        result = self.storage.send_message(
            sender=msg.sender,
            recipient=request.recipient,
            message=msg.message,
            status="replicated",
            message_id=msg.id 
        )
        return chat_pb2.Response(status=result["status"], message="Replication successful.")

    def ListAccounts(self, request, context):
        response = self.storage.list_accounts(request.page_num)
        return chat_pb2.ListAccountsResponse(usernames=response["message"])

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
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def DeleteAccount(self, request, context):
        response = self.storage.delete_account(request.username, request.password)
        if response["status"] == "success":
            self.online_users.pop(request.username, None)
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

def serve(is_leader=False, replica_addresses=None, port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(is_leader, replica_addresses), server)
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
    parser.add_argument('--leader', action='store_true')
    parser.add_argument('--port', type=int, default=50051)
    parser.add_argument('--replicas', nargs='*', default=[])
    args = parser.parse_args()
    serve(is_leader=args.leader, replica_addresses=args.replicas, port=args.port)