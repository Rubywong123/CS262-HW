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
            CustomProtocol.send(self.client, request)
            response = CustomProtocol.receive(self.client)

        if response["status"] == "success":
            self.username = username
            self.label.config(text=f"Logged in as {username}")
        else:
            self.label.config(text="Login failed")


if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()
    client = ChatClient(root, args)
    root.mainloop()
