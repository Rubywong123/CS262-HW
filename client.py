import socket
import json
import tkinter as tk
from protocol import JSONProtocol, CustomProtocol

HOST = '127.0.0.1'
PORT = 65432
USE_JSON = True  # Toggle between JSON and Custom protocol

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client")
        self.username = None
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((HOST, PORT))
        
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
        
        if USE_JSON:
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

root = tk.Tk()
client = ChatClient(root)
root.mainloop()
