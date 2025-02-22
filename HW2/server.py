import grpc
from concurrent import futures
import time
import chat_pb2
import chat_pb2_grpc
from storage import Storage
from queue import Queue, Empty

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.storage = Storage("data.db")
        self.online_users = {}

    def Login(self, request, context):
        response = self.storage.login_register_user(request.username, request.password)
        if response["status"] == "success":
            self.online_users[request.username] = context  # Store user session
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def SendMessage(self, request, context):
        sender = request.username
        recipient = request.recipient
        message = request.message

        if recipient in self.online_users and isinstance(self.online_users[recipient], Queue):
            self.online_users[recipient].put({"sender": sender, "message": message})
            print(f"Real-time message delivered to {recipient}")
            return chat_pb2.Response(status="success", message="Message delivered in real-time.")

        self.storage.send_message(sender, recipient, message)
        print(f"Message stored for offline user {recipient}")

        return chat_pb2.Response(status="success", message="Message stored for later delivery.")


    def ReadMessages(self, request, context):
        """ Fetch unread messages only when the user explicitly requests them. """
        messages = self.storage.read_messages(request.username, request.limit)
        return chat_pb2.ReadMessagesResponse(
            messages=[
                chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"])
                for msg in messages.get("messages", [])
            ]
        )

    def ListenForMessages(self, request, context):
        """ Streaming RPC: Sends real-time messages to online users using a queue. """
        username = request.username

        # Ensure the user is assigned a queue, not a context object
        if username not in self.online_users or not isinstance(self.online_users[username], Queue):
            self.online_users[username] = Queue()  # Always store a Queue

        print(f"{username} is now listening for messages...")

        try:
            while True:
                try:
                    message = self.online_users[username].get(timeout=10)  # Get message from queue
                    yield chat_pb2.Message(id=-1, sender=message["sender"], message=message["message"])
                except Empty:
                    continue  # No new messages yet, keep waiting
        except grpc.RpcError:
            print(f"{username} has disconnected.")
            del self.online_users[username]  # Remove user from online list when they disconnect

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
