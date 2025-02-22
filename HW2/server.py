import grpc
from concurrent import futures
import time
import chat_pb2
import chat_pb2_grpc
from storage import Storage
import queue

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.storage = Storage("data.db")
        self.online_users = {}  # username -> queue of messages

    def Login(self, request, context):
        response = self.storage.login_register_user(request.username, request.password)
        if response["status"] == "success":
            self.online_users[request.username] = queue.Queue()  # Use thread-safe Queue
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def SendMessage(self, request, context):
        sender = request.username
        recipient = request.recipient
        message = request.message

        if recipient in self.online_users:
            try:
                self.online_users[recipient].put(chat_pb2.Message(id=int(time.time()), sender=sender, message=message))
                self.storage.send_message(sender, recipient, message, status='read')
                return chat_pb2.Response(status="success", message="Message delivered in real-time.")
            except queue.Full:
                pass  # If the queue is full, fallback to storing

        self.storage.send_message(sender, recipient, message)
        return chat_pb2.Response(status="success", message="Message stored for later delivery.")

    
    def ListAccounts(self, request, context):
        response = self.storage.list_accounts(request.page_num)
        return chat_pb2.ListAccountsResponse(usernames=response["message"])


    def ReadMessages(self, request, context):
        messages = self.storage.read_messages(request.username, request.limit)
        
        return chat_pb2.ReadMessagesResponse(
            status=messages["status"],
            messages=[
                chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"])
                for msg in messages.get("messages", [])
            ]
        )

    def ListenForMessages(self, request, context):
        """ Streams new messages in real-time using a thread-safe Queue. """
        username = request.username
        if username not in self.online_users:
            context.abort(grpc.StatusCode.NOT_FOUND, "User not logged in")

        q = self.online_users[username]

        while True:
            try:
                message = q.get(timeout=10)  # Block until a message arrives
                yield message  # Stream the message to the client
            except queue.Empty:
                pass  # Continue waiting for new messages
            except grpc.RpcError:
                del self.online_users[username]  # Remove disconnected users
                break

    def DeleteMessage(self, request, context):
        response = self.storage.delete_message(request.username, request.recipient, request.message_id)
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
