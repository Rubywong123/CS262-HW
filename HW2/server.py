import grpc
from concurrent import futures
import time
import chat_pb2
import chat_pb2_grpc
from storage import Storage

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.storage = Storage("data.db")
        self.logged_in_users = {}

    def Login(self, request, context):
        response = self.storage.login_register_user(request.username, request.password)
        if response["status"] == "success":
            self.logged_in_users[request.username] = True
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def ListAccounts(self, request, context):
        response = self.storage.list_accounts(request.page_num)
        return chat_pb2.ListAccountsResponse(usernames=response["message"])

    def SendMessage(self, request, context):
        response = self.storage.send_message(request.username, request.recipient, request.message)
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def ReadMessages(self, request, context):
        response = self.storage.read_messages(request.username, request.limit)
        messages = [chat_pb2.Message(id=msg["id"], sender=msg["sender"], message=msg["message"]) for msg in response.get("messages", [])]
        return chat_pb2.ReadMessagesResponse(messages=messages)

    def DeleteMessage(self, request, context):
        response = self.storage.delete_message(request.username, request.recipient, request.message_id)
        return chat_pb2.Response(status=response["status"], message=response.get("message", ""))

    def DeleteAccount(self, request, context):
        response = self.storage.delete_account(request.username, request.password)
        if response["status"] == "success":
            self.logged_in_users.pop(request.username, None)
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
