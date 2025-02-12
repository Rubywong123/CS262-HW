import socket
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import simpledialog
from protocol import JSONProtocol, CustomProtocol
from argparse import ArgumentParser
import threading
import queue
import time

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
    def __init__(self, args, master):
        self.args = args
        self.master = master
        self.master.title("Chat Client")
        
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((args.host, args.port))
        self.username = None
        self.message_queue = queue.Queue()
        
        self.create_login_screen()
        
    def create_login_screen(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        
        tk.Label(self.master, text="Enter Username:").pack()
        self.username_entry = tk.Entry(self.master)
        self.username_entry.pack()
        
        tk.Label(self.master, text="Enter Password:").pack()
        self.password_entry = tk.Entry(self.master, show='*')
        self.password_entry.pack()
        
        tk.Button(self.master, text="Login/Register", command=self.authenticate).pack()
    
    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Username and Password cannot be empty!")
            return
        
        request = {"action": "login", "username": username, "password": password}
        if self.args.json:
            JSONProtocol.send(self.client, request)
            response = JSONProtocol.receive(self.client)
        else:
            CustomProtocol.send(self.client, LOGIN, username=username, password=password)
            response = CustomProtocol.receive(self.client)
        
        if response["status"] == "success":
            self.username = username
            messagebox.showinfo("Success", f"Logged in as {username}")
            threading.Thread(target=self.listen_for_messages, daemon=True).start()
            self.create_main_screen()
        else:
            messagebox.showerror("Login Failed", response["message"])

    def create_main_screen(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        
        self.chat_log = scrolledtext.ScrolledText(self.master, state=tk.DISABLED, height=15)
        self.chat_log.pack()
        
        tk.Button(self.master, text="List Accounts", command=self.list_accounts).pack()
        tk.Button(self.master, text="Send Message", command=self.send_message).pack()
        tk.Button(self.master, text="Read Messages", command=self.read_messages).pack()
        tk.Button(self.master, text="Delete Message", command=self.delete_message).pack()
        tk.Button(self.master, text="Delete Account", command=self.delete_account).pack()
    
    def update_chat_log(self, message):
        self.chat_log.config(state=tk.NORMAL)
        self.chat_log.insert(tk.END, message + "\n")
        self.chat_log.config(state=tk.DISABLED)
    
    def list_accounts(self):
        request = {'action_type': LIST_ACCOUNTS, 'page_num': 1}
        self.send_request(request)
        response = self.check_incoming_message()
        if response["status"] == "success":
            self.update_chat_log("Accounts: " + ", ".join(response["message"]))
    
    # def send_message(self):
    #     recipient = simple_input("Enter recipient username:")
    #     message = simple_input("Enter message:")
    #     if recipient and message:
    #         request = {'action_type': SEND_MESSAGE, "recipient": recipient, "message": message}
    #         self.send_request(request)
    
    # def read_messages(self):
    #     request = {"action_type": READ_MESSAGES, 'limit': 5}
    #     self.send_request(request)
    #     response = self.check_incoming_message()
    #     if response["status"] == "success":
    #         for msg in response["messages"]:
    #             self.update_chat_log(f"From {msg['sender']}: {msg['message']}")
    
    def delete_message(self):
        message_id = simple_input("Enter message ID to delete:")
        if message_id:
            request = {"action_type": DELETE_MESSAGE, "message_id": int(message_id)}
            self.send_request(request)
    
    def delete_account(self):
        password = simple_input("Enter your password to delete account:")
        if password:
            request = {"action_type": DELETE_ACCOUNT, "password": password}
            self.send_request(request)
            
            response = JSONProtocol.receive(self.client) if self.args.json else CustomProtocol.receive(self.client)
            
            if response and response.get("status") == "success":
                self.client.close()
                self.master.quit()
    
    def send_request(self, request):
        if self.args.json:
            action = request.pop('action_type', None)
            action = action_map[action]
            request = {"action": action, **request}
            JSONProtocol.send(self.client, **request)
        else:
            action_type = request.pop('action_type', None)
            CustomProtocol.send(self.client, action_type, **request)

    # def listen_for_messages(self):
    #     while True:
    #         try:
    #             response = JSONProtocol.receive(self.client) if self.args.json else CustomProtocol.receive(self.client)
    #             if response:
    #                 # Extract message only if response contains 'status' and 'message'
    #                 if response.get("status") == "New message" and "message" in response:
    #                     self.update_chat_log(response["message"])  # Show only the message
    #                 else:
    #                     self.update_chat_log(f"[Server]: {response}")  # Default logging
    #         except Exception as e:
    #             self.update_chat_log("[Error]: Disconnected from server.")
    #             break

    def listen_for_messages(self):
        while True:
            try:
                response = JSONProtocol.receive(self.client) if self.args.json else CustomProtocol.receive(self.client)
                if response:
                    if response.get("action") == "response":
                        status = response.get("status")
                        message = response.get("message")
                        
                        if status == "New message":
                            self.update_chat_log(message)
                        elif status == "success":
                            if message is None:
                                pass
                            elif isinstance(message, str) and message.startswith('['):
                                try:
                                    import ast
                                    messages = ast.literal_eval(message)
                                    for msg in messages:
                                        self.update_chat_log(f"From {msg['sender']}: {msg['message']}")
                                except:
                                    self.update_chat_log(f"[Server]: {message}")
                            else:
                                self.update_chat_log(f"[Server]: {message}")
                        else:
                            if message:
                                self.update_chat_log(f"[Server]: {message}")
                    else:
                        if str(response) != "None" and response:
                            self.update_chat_log(f"[Server]: {response}")
            except Exception as e:
                print(f"Error in listen_for_messages: {e}")
                self.update_chat_log(f"[Error]: Disconnected from server. {str(e)}")
                break

    def send_message(self):
        recipient = simple_input("Enter recipient username:")
        message = simple_input("Enter message:")
        if recipient and message:
            request = {'action_type': SEND_MESSAGE, "recipient": recipient, "message": message}
            self.send_request(request)
            # Add a local echo of the sent message
            self.update_chat_log(f"To {recipient}: {message}")

    def read_messages(self):
        request = {"action_type": READ_MESSAGES, 'limit': 5}
        self.send_request(request)

    
    def check_incoming_message(self):
        time.sleep(1)
        while not self.message_queue.empty():
            return self.message_queue.get()
        return {"status": "error", "message": "No response"}

def simple_input(prompt):
    return simpledialog.askstring("Input", prompt)

if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()
    client = ChatClient(args, root)
    root.mainloop()
