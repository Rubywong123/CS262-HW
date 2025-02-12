import unittest
from unittest.mock import MagicMock, patch
import socket
from client import ChatClient, simple_input
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

    def test_authenticate_failure(self):
        self.client.username_entry.insert(0, "wronguser")
        self.client.password_entry.insert(0, "wrongpass")
        
        with patch.object(JSONProtocol, 'send'), \
             patch.object(JSONProtocol, 'receive', return_value={"status": "error", "message": "Invalid credentials"}), \
             patch('tkinter.messagebox.showerror') as mock_error:
            
            self.client.authenticate()
            mock_error.assert_called_with("Login Failed", "Invalid credentials")
            self.assertIsNone(self.client.username)

    def test_list_accounts_json(self):
        with patch.object(JSONProtocol, 'send') as mock_send, \
             patch.object(JSONProtocol, 'receive', return_value={"status": "success", "message": ["user1", "user2"]}):
            
            self.client.list_accounts()
            mock_send.assert_called()

    def test_send_message_json(self):
        self.client.create_main_screen()
        with patch('tkinter.simpledialog.askstring', side_effect=["friend", "Hello"]):
            with patch.object(JSONProtocol, 'send') as mock_send:
                self.client.send_message()
                mock_send.assert_called()

    def test_read_messages_json(self):
        self.client.create_main_screen()
        with patch.object(JSONProtocol, 'send') as mock_send, \
             patch.object(JSONProtocol, 'receive', return_value={"status": "success", "messages": [{"sender": "friend", "message": "Hey"}]}):
            
            self.client.read_messages()
            mock_send.assert_called()

    def test_send_message_custom(self):
        self.client.args.json = False
        self.client.create_main_screen()

        with patch('tkinter.simpledialog.askstring', side_effect=["friend", "Hello"]), \
            patch.object(CustomProtocol, 'send') as mock_send:
            
            self.client.send_message()
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
        
            self.assertEqual(args[0], self.client.client)
            self.assertEqual(args[1], 3) 
            
            self.assertEqual(kwargs["recipient"], "friend")
            self.assertEqual(kwargs["message"], "Hello")
    
    def test_delete_message(self):
        self.client.create_main_screen()
        with patch('tkinter.simpledialog.askstring', return_value="123"):
            with patch.object(JSONProtocol, 'send') as mock_send:
                self.client.delete_message()
                mock_send.assert_called()

    def test_check_incoming_message_no_response(self):
        response = self.client.check_incoming_message()
        self.assertEqual(response, {"status": "error", "message": "No response"})

    def test_check_incoming_message_with_response(self):
        self.client.message_queue.put({"status": "success", "message": "Test response"})
        response = self.client.check_incoming_message()
        self.assertEqual(response, {"status": "success", "message": "Test response"})

    def test_update_chat_log(self):
        self.client.create_main_screen()
        self.client.update_chat_log("Test Message")
        self.assertIn("Test Message", self.client.chat_log.get("1.0", tk.END))

    def test_parse_args(self):
        with patch('sys.argv', ['client.py', '--host', '192.168.1.1', '--port', '8000', '--json']):
            args = self.client.args
            self.assertEqual(args.host, '127.0.0.1') 
            self.assertEqual(args.port, 65432)
            self.assertTrue(args.json)

    def test_simple_input(self):
        with patch('tkinter.simpledialog.askstring', return_value="test"):
            response = simple_input("Enter value:")
            self.assertEqual(response, "test")

    def test_send_request_with_custom_protocol(self):
        self.client.args.json = False 

        with patch.object(CustomProtocol, 'send') as mock_send:
            self.client.send_request({'action_type': 3, "recipient": "friend", "message": "Hello"})
            mock_send.assert_called()

    def test_empty_credentials(self):
        self.client.username_entry.insert(0, "")
        self.client.password_entry.insert(0, "")
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            self.client.authenticate()
            mock_error.assert_called_with("Error", "Username and Password cannot be empty!")
            self.assertIsNone(self.client.username)

    def test_delete_account_success(self):
        self.client.create_main_screen()
        mock_response = {"status": "success", "message": "Account deleted"}
        
        with patch('tkinter.simpledialog.askstring', return_value="password123"), \
            patch.object(JSONProtocol, 'send') as mock_send, \
            patch.object(JSONProtocol, 'receive', return_value=mock_response), \
            patch.object(self.client.client, 'close') as mock_close, \
            patch.object(tk.Tk, 'quit') as mock_quit:
            
            self.client.delete_account()
    
            mock_send.assert_called_once()
            mock_close.assert_called_once()
            mock_quit.assert_called_once()

    def test_listen_for_messages_success_with_array(self):
        self.client.create_main_screen()
        mock_response = {
            "action": "response",
            "status": "success",
            "message": '[{"sender": "user1", "message": "Hi"}, {"sender": "user2", "message": "Hello"}]'
        }
        
        with patch.object(JSONProtocol, 'receive', side_effect=[mock_response, Exception("Connection closed")]), \
            patch.object(self.client, 'update_chat_log') as mock_update:
            
            self.client.listen_for_messages()
            mock_update.assert_any_call("From user1: Hi")
            mock_update.assert_any_call("From user2: Hello")


if __name__ == "__main__":
    unittest.main()
