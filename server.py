import socket
import threading
import json
import struct
from storage import Storage
from protocol import CustomProtocol, JSONProtocol

from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--host", default='127.0.0.1', help="Host address")
    parser.add_argument("--port", default=65432, help="Port number")
    parser.add_argument("--json", action="store_true", help="Use JSON protocol")
    return parser.parse_args()

class ChatServer:
    def __init__(self, args):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = args.host
        self.port = args.port
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        self.clients = {}
        self.use_json = args.json
        self.login_users = []

    def handle_client(self, client_socket):
        storage = Storage("data.db")  # SQLite database for user accounts and messages
        try:
            while True:
                if self.use_json:
                    data = JSONProtocol.receive(client_socket)
                else:
                    data = CustomProtocol.receive(client_socket)

                if not data:
                    break

                action = data.get("action")
                if action == "login":
                    response = storage.login_register_user(data["username"], data["password"])
                    # record the login status
                    if response["status"] == "success":
                        self.login_users.append(data["username"])

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
                    CustomProtocol.send(client_socket, 7,response)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    def start(self):
        print(f"Server running on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server.accept()
            print(f"New connection from {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

if __name__ == "__main__":
    args = parse_args()
    server = ChatServer(args)
    server.start()
