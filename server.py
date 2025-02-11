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
        
        self.use_json = args.json
        # map the ip address and port of the client to the username
        self.login_users = {}
        # map the ip address and port of the client to the client socket
        self.clients_sockets = {}


    def handle_client(self, client_socket):
        storage = Storage("data.db")  # SQLite database for user accounts and messages
        addr = f'{client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}'  # IP address and port of the client
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
                        # get ip address and port of the client
                        ip = client_socket.getpeername()[0]
                        port = client_socket.getpeername()[1]
                        print(f"User {data['username']} logged in from {addr}")
                        self.login_users[addr] = data["username"]

                elif action == "list_accounts":
                    response = storage.list_accounts(data['page_num'])
                elif action == "send_message":
                    sender = self.login_users.get(addr)
                    # check if the recipient logged in
                    # if logged in, directly send the message
                    if data["recipient"] in self.login_users.values():
                        response = {"status": "New message", 'message': f"{sender}: {data['message']}"}
                        # find the target client socket
                        addr = list(self.login_users.keys())[list(self.login_users.values()).index(data["recipient"])]
                        recipient_socket = self.clients_sockets[addr]
                        if self.use_json:
                            JSONProtocol.send(recipient_socket, response)
                        else:
                            CustomProtocol.send(recipient_socket, 7, **response)
                        # if not logged in, store the message
                    response = storage.send_message(sender, data["recipient"], data["message"])
                elif action == "read_messages":
                    user = self.login_users.get(addr)
                    response = storage.read_messages(user, data.get("limit", 10))
                elif action == "delete_message":
                    user = self.login_users.get(addr)
                    response = storage.delete_message(user, data['recipient'], data["message_id"])
                elif action == "delete_account":
                    user = self.login_users.get(addr)
                    response = storage.delete_account(user, data["password"])
                    # remove the user from the login_users
                    if response["status"] == "success":
                        self.login_users.pop(addr)
                
                else:
                    response = {"status": "error", "message": "Unknown action"}
                
                if self.use_json:
                    JSONProtocol.send(client_socket, response)
                else:
                    if not response or "status" not in response:
                        response = {"status": "error", "message": "Invalid response from server"}
                    CustomProtocol.send(client_socket, 7, **response)

                if action == "delete_account" and response["status"] == "success":
                    break

        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    def start(self):
        print(f"Server running on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server.accept()
            print(f"New connection from {addr}")
            addr = f'{addr[0]}:{addr[1]}'
            self.clients_sockets[addr] = client_socket
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

if __name__ == "__main__":
    args = parse_args()
    server = ChatServer(args)
    server.start()
