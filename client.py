import socket
import json
import tkinter as tk
from protocol import JSONProtocol, CustomProtocol
from argparse import ArgumentParser
import threading
import queue
import time
import bcrypt

LOGIN = 1
LIST_ACCOUNTS = 2
SEND_MESSAGE = 3
READ_MESSAGES = 4
DELETE_MESSAGE = 5
DELETE_ACCOUNT = 6
action_map = {
    1: "login",
    2: "list_accounts",
    3: "send_message",
    4: "read_messages",
    5: "delete_message",
    6: "delete_account",
}

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--host", default='127.0.0.1', help="Host address")
    parser.add_argument("--port", default=65432, help="Port number")
    parser.add_argument("--json", action="store_true", help="Use JSON protocol")

    return parser.parse_args()


class ChatClient:
    # TODO: GUI support
    def __init__(self, args, master=None):
        # self.master = master
        # self.master.title("Chat Client")


        self.username = None
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((args.host, args.port))

        self.message_queue = queue.Queue()
        
        # self.label = tk.Label(master, text="Enter Username:")
        # self.label.pack()
        
        # self.entry = tk.Entry(master)
        # self.entry.pack()
        
        # self.button = tk.Button(master, text="Login/Register", command=self.authenticate)
        # self.button.pack()
        
        # self.text = tk.Text(master, state=tk.DISABLED)
        # self.text.pack()

    

    def authenticate(self):
        # username = self.entry.get()
        login = False
        while not login:
            print("Welcome to the chat client!")
            username = input("Enter username: ")
            password = input("Enter password: ")

            # encrypt the password
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

            request = {"action": "login", "username": username, "password": password_hash}
            
            if args.json:
                JSONProtocol.send(self.client, request)
                response = JSONProtocol.receive(self.client)
            else:
                CustomProtocol.send(self.client, LOGIN, username=username, password=password)
                response = CustomProtocol.receive(self.client)
            print(response)    

            if response["status"] == "success":
                login = True
                self.username = username
                print(f"##########Logged in as {username}##########")
                # self.label.config(text=f"Logged in as {username}")
                # listen for messages from the server
                listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
                listener_thread.start()
                self.create_terminal_interface()

            else:
                print("Login failed: ", response["message"])
                # self.label.config(text="Login failed")

    def create_terminal_interface(self):
        while True:
            print("Choose an action:")
            print("1. List accounts")
            print("2. Send message")
            print("3. Read messages")
            print("4. Delete message")
            print("5. Delete account")
            print("6. Exit")
            choice = input("Enter the number of the action: ")

            if choice == '1':
                self.list_accounts()
            elif choice == '2':
                self.send_message()
            elif choice == '3':
                self.read_messages()
            elif choice == '4':
                self.delete_message()
            elif choice == '5':
                self.delete_account()
            elif choice == '6':
                self.client.close()
                exit(0)
            else:
                print("Invalid choice. Please try again.")

    def list_accounts(self):
        page_num = 1
        request = {'action_type': LIST_ACCOUNTS, 'page_num': page_num}
        self.send_request(request)
        response = self.check_incoming_message()
        r = ''
        
        while response["status"] == "success":
            
            print(f"Page {page_num}")
            print("Accounts:", response["message"])
            # wait for user input to continue
            command = input("Press 'n' to view the next page, 'b' to view the previous page, or press 'q' to quit: ")
            if command == 'q':
                break
            elif command == 'n':
                page_num += 1
            elif command == 'b':
                page_num = max(1, page_num - 1)
            request = {'action_type': LIST_ACCOUNTS, 'page_num': page_num}
            self.send_request(request)

            response = self.check_incoming_message()

    def send_message(self):
        recipient = input("Enter the recipient username: ")
        message = input("Enter the message: ")
        request = {'action_type': SEND_MESSAGE, "recipient": recipient, "message": message}
        self.send_request(request)

        response = self.check_incoming_message()

    def read_messages(self):
        number = input("Enter the number of messages to read: ")
        request = {"action_type": READ_MESSAGES, 'limit': int(number)}
        self.send_request(request)

        response = self.check_incoming_message()


    def delete_message(self):
        recipient = input("Enter the recipient username: ")
        message_id = input("Enter the message ID to delete: ")
        request = {"action_type": DELETE_MESSAGE, "recipient": recipient,  "message_id": int(message_id)}
        self.send_request(request)

        response = self.check_incoming_message()

    def delete_account(self):
        password = input("Enter your password to delete your account: ")
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        request = {"action_type": DELETE_ACCOUNT, "password": password_hash}
        self.send_request(request)

        response = self.check_incoming_message()
        if response["status"] == "success":
            self.client.close()
            exit(0)


    def send_request(self, request):
        if args.json:
            action = request.pop('action_type', None)
            action = action_map[action]
            request = {"action": action, **request}
            JSONProtocol.send(self.client, **request)
        else:
            action_type = request.pop('action_type', None)
            CustomProtocol.send(self.client, action_type, **request)

    def listen_for_messages(self):
        """Continuously listens for messages from the server."""
        while True:
            try:
                if args.json:
                    response = JSONProtocol.receive(self.client)
                else:
                    response = CustomProtocol.receive(self.client)

                if response:
                    print("\n[Server]:", response)
                    self.message_queue.put(response)
            except Exception as e:
                print("[Error]: Disconnected from server.", e)
                break

    def check_incoming_message(self):
        time.sleep(1)
        while not self.message_queue.empty():
            message = self.message_queue.get()
        return message


if __name__ == "__main__":
    args = parse_args()
    # root = tk.Tk()
    client = ChatClient(args)

    client.authenticate()
