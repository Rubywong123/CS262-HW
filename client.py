import socket
import json
import tkinter as tk
from protocol import JSONProtocol, CustomProtocol
from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--host", default='127.0.0.1', help="Host address")
    parser.add_argument("--port", default=65432, help="Port number")
    parser.add_argument("--json", action="store_true", help="Use JSON protocol")

    return parser.parse_args()


class ChatClient:
    def __init__(self, master, args):
        self.master = master
        self.master.title("Chat Client")
        self.username = None
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((args.host, args.port))
        
        self.label = tk.Label(master, text="Enter Username:")
        self.label.pack()
        
        self.entry = tk.Entry(master)
        self.entry.pack()
        
        self.button = tk.Button(master, text="Login/Register", command=self.authenticate)
        self.button.pack()
        
        self.text = tk.Text(master, state=tk.DISABLED)
        self.text.pack()

    

    def authenticate(self):
        username = self.entry.get()
        password = "password123"  # Normally, prompt for password securely
        request = {"action": "login", "username": username, "password": password}
        
        if args.json:
            JSONProtocol.send(self.client, request)
            response = JSONProtocol.receive(self.client)
        else:
            action_type = 1
            CustomProtocol.send(self.client, action_type, username=username, password=password)
            response = CustomProtocol.receive(self.client)

        if response["status"] == "success":
            self.username = username
            self.label.config(text=f"Logged in as {username}")
        else:
            self.label.config(text="Login failed")
            self.create_terminal_interface()

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
                break
            else:
                print("Invalid choice. Please try again.")

        def list_accounts(self):
            request = {"action": "list_accounts"}
            response = self.send_request(request)
            

        def send_message(self):
            recipient = input("Enter the recipient username: ")
            message = input("Enter the message: ")
            request = {"action": "send_message", "recipient": recipient, "message": message}
            response = self.send_request(request)

        def read_messages(self):
            number = input("Enter the number of messages to read: ")
            request = {"action": "read_messages", 'limit': int(number)}
            response = self.send_request(request)


        def delete_message(self):
            message_id = input("Enter the message ID to delete: ")
            request = {"action": "delete_message", "message_id": message_id}
            response = self.send_request(request)

        def delete_account(self):
            request = {"action": "delete_account", "username": self.username}
            response = self.send_request(request)

    def send_request(self, request):
        if args.json:
            JSONProtocol.send(self.client, request)
            response = JSONProtocol.receive(self.client)
        else:
            CustomProtocol.send(self.client, request)
            response = CustomProtocol.receive(self.client)

        print("Server response:", response)

        return response

if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()
    client = ChatClient(root, args)
    root.mainloop()
