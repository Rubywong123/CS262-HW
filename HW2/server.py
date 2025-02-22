import grpc
from concurrent import futures
import time
import chat_pb2
import chat_pb2_grpc
from storage import Storage

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.storage = Storage("data.db")
        self.online_users = {}  # Track online users (username -> response stream)

    def Login(self, request, context):
        response = self.storage.login_register_user(request.username, request.password)
        if response["status"] == "success":
            self.online_users[request.username] = context  # Store user session
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def SendMessage(self, request, context):
        sender = request.username
        recipient = request.recipient
        message = request.message

        # If recipient is online, send the message immediately
        if recipient in self.online_users:
            try:
                print(f"Delivering message to online user {recipient}")
                return chat_pb2.Response(status="success", message="Message delivered immediately.")
            except grpc.RpcError:
                del self.online_users[recipient]  # Remove disconnected users

        # Store the message for offline retrieval
        self.storage.send_message(sender, recipient, message)
        print(f"Message stored for offline user {recipient}")

        return chat_pb2.Response(status="success", message="Message stored for later delivery.")



    def ReadMessages(self, request, context):
        messages = self.storage.read_messages(request.username, request.limit)
        return chat_pb2.ReadMessagesResponse(
            messages=[
                chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"])
                for msg in messages.get("messages", [])
            ]
        )

    def ListenForMessages(self, request, context):
        """ Streaming RPC: Sends messages to online users in real-time """
        username = request.username
        while True:
            if username in self.online_users:
                try:
                    messages = self.storage.read_messages(username, 10).get("messages", [])
                    for msg in messages:
                        yield chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"])
                    
                    time.sleep(2)  # Poll every 2 seconds
                except grpc.RpcError:
                    del self.online_users[username]  # Remove disconnected users
                    break

    def DeleteMessage(self, request, context):
        response = self.storage.delete_message(request.username, request.message_id)
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def DeleteAccount(self, request, context):
        response = self.storage.delete_account(request.username, request.password)
        if response["status"] == "success":
            self.online_users.pop(request.username, None)  # Remove from online users
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port("[::]:50051")
    print("Starting gRPC server on port 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
