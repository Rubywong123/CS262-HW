import socket
import threading
import json
import struct
from storage import Storage
from protocol import CustomProtocol, JSONProtocol

HOST = '127.0.0.1'
PORT = 65432
storage = Storage("data.db")  # SQLite database for user accounts and messages

class ChatServer:
    def __init__(self, host, port, use_json=True):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = {}
        self.use_json = use_json

    def handle_client(self, client_socket):
        try:
            while True:
                if self.use_json:
                    data = JSONProtocol.receive(client_socket)
                else:
                    data = CustomProtocol.receive(client_socket)

                if not data:
                    break

                action = data.get("action")
                if action == "register":
                    response = storage.register_user(data["username"], data["password"])
                elif action == "login":
                    response = storage.login_user(data["username"], data["password"])
                elif action == "list_accounts":
                    response = storage.list_accounts(data.get("pattern", ""))
                elif action == "send_message":
                    response = storage.send_message(data["sender"], data["recipient"], data["message"])
                elif action == "read_messages":
                    response = storage.get_messages(data["username"], data.get("limit", 10))
                elif action == "delete_message":
                    response = storage.delete_message(data["username"], data["message_id"])
                elif action == "delete_account":
                    response = storage.delete_account(data["username"], data["password"])
                else:
                    response = {"status": "error", "message": "Unknown action"}

                if self.use_json:
                    JSONProtocol.send(client_socket, response)
                else:
                    CustomProtocol.send(client_socket, response)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    def start(self):
        print(f"Server running on {HOST}:{PORT}")
        while True:
            client_socket, addr = self.server.accept()
            print(f"New connection from {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

if __name__ == "__main__":
    server = ChatServer(HOST, PORT, use_json=True)
    server.start()
