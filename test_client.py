import unittest
from unittest.mock import MagicMock, patch
import socket
from client import ChatClient
from protocol import JSONProtocol, CustomProtocol
from argparse import Namespace
import tkinter as tk

class TestChatClient(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.mock_socket = MagicMock(spec=socket.socket)
        args = Namespace(host='127.0.0.1', port=65432, json=True)
        
        with patch('socket.socket', return_value=self.mock_socket):
            self.client = ChatClient(args, self.root)

    def tearDown(self):
        self.root.destroy()

    def test_authenticate_success_json(self):
        self.client.username_entry.insert(0, "testuser")
        self.client.password_entry.insert(0, "testpass")
        
        with patch.object(JSONProtocol, 'send') as mock_send, \
             patch.object(JSONProtocol, 'receive', return_value={"status": "success"}):
            
            self.client.authenticate()
            self.assertEqual(self.client.username, "testuser")
            mock_send.assert_called()
    
    def test_authenticate_success_custom(self):
        self.client.args.json = False
        self.client.username_entry.insert(0, "testuser")
        self.client.password_entry.insert(0, "testpass")
        
        with patch.object(CustomProtocol, 'send') as mock_send, \
             patch.object(CustomProtocol, 'receive', return_value={"status": "success"}):
            
            self.client.authenticate()
            self.assertEqual(self.client.username, "testuser")
            mock_send.assert_called()
    
    def test_send_message_json(self):
        self.client.create_main_screen()
        with patch('tkinter.simpledialog.askstring', side_effect=["friend", "Hello"]):
            with patch.object(JSONProtocol, 'send') as mock_send:
                self.client.send_message()
                mock_send.assert_called()
    
    def test_send_message_custom(self):
        self.client.args.json = False
        self.client.create_main_screen()
        with patch('tkinter.simpledialog.askstring', side_effect=["friend", "Hello"]):
            with patch.object(CustomProtocol, 'send') as mock_send:
                self.client.send_message()
                mock_send.assert_called()
    
    def test_list_accounts_json(self):
        with patch.object(JSONProtocol, 'send') as mock_send, \
             patch.object(JSONProtocol, 'receive', return_value={"status": "success", "message": ["user1", "user2"]}):
            
            self.client.list_accounts()
            mock_send.assert_called()
    
    def test_list_accounts_custom(self):
        self.client.args.json = False
        with patch.object(CustomProtocol, 'send') as mock_send, \
             patch.object(CustomProtocol, 'receive', return_value={"status": "success", "message": ["user1", "user2"]}):
            
            self.client.list_accounts()
            mock_send.assert_called()

if __name__ == "__main__":
    unittest.main()
