import unittest
from unittest.mock import MagicMock, patch
import socket
from server import ChatServer
from protocol import JSONProtocol, CustomProtocol
from argparse import Namespace

class TestChatServer(unittest.TestCase):
    def setUp(self):
        args = Namespace(host='127.0.0.1', port=65432, json=True)
        with patch('socket.socket') as mock_socket:
            self.server = ChatServer(args)
            self.server.server = mock_socket
        self.mock_client_socket = MagicMock(spec=socket.socket)
        self.mock_client_socket.getpeername.return_value = ("127.0.0.1", 1234)
        self.server.clients_sockets = {}
        self.server.login_users = {"127.0.0.1:1234": "testuser"}
    
    def test_handle_login_json(self):
        self.server.use_json = True
        with patch.object(JSONProtocol, 'receive', side_effect=[{"action": "login", "username": "testuser", "password": "testpass"}, None]), \
             patch.object(JSONProtocol, 'send') as mock_send, \
             patch('server.Storage') as mock_storage:
            
            mock_storage.return_value.login_register_user.return_value = {"status": "success"}
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called()
    
    def test_handle_login_custom(self):
        self.server.use_json = False
        with patch.object(CustomProtocol, 'receive', side_effect=[{"action": "login", "username": "testuser", "password": "testpass"}, None]), \
             patch.object(CustomProtocol, 'send') as mock_send, \
             patch('server.Storage') as mock_storage:
            
            mock_storage.return_value.login_register_user.return_value = {"status": "success"}
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called()
    
    def test_handle_send_message_json(self):
        self.server.use_json = True
        self.server.login_users["127.0.0.1:1234"] = "testuser"
        with patch.object(JSONProtocol, 'receive', side_effect=[{"action": "send_message", "recipient": "friend", "message": "Hello"}, None]), \
             patch.object(JSONProtocol, 'send') as mock_send, \
             patch('server.Storage') as mock_storage:
            
            mock_storage.return_value.send_message.return_value = {"status": "success"}
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called()

    def test_handle_read_messages_json(self):
        self.server.use_json = True
        with patch.object(JSONProtocol, 'receive', side_effect=[{"action": "read_messages", "limit": 5}, None]), \
             patch.object(JSONProtocol, 'send') as mock_send, \
             patch('server.Storage') as mock_storage:
            
            mock_storage.return_value.read_messages.return_value = {"status": "success", "messages": [{"sender": "friend", "message": "Hey"}]}
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called()

    def test_handle_list_accounts_json(self):
        self.server.use_json = True
        with patch.object(JSONProtocol, 'receive', side_effect=[{"action": "list_accounts", "page_num": 1}, None]), \
             patch.object(JSONProtocol, 'send') as mock_send, \
             patch('server.Storage') as mock_storage:
            
            mock_storage.return_value.list_accounts.return_value = {"status": "success", "message": ["user1", "user2"]}
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called()

    def test_handle_delete_message_json(self):
        self.server.use_json = True
        with patch.object(JSONProtocol, 'receive', side_effect=[{"action": "delete_message", "recipient": "friend", "message_id": 123}, None]), \
             patch.object(JSONProtocol, 'send') as mock_send, \
             patch('server.Storage') as mock_storage:
            
            mock_storage.return_value.delete_message.return_value = {"status": "success"}
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called()
    
    def test_handle_delete_account_json(self):
        self.server.use_json = True
        self.server.login_users["127.0.0.1:1234"] = "testuser"
        with patch.object(JSONProtocol, 'receive', side_effect=[{"action": "delete_account", "password": "testpass"}, None]), \
             patch.object(JSONProtocol, 'send') as mock_send, \
             patch('server.Storage') as mock_storage:
            
            mock_storage.return_value.delete_account.return_value = {"status": "success"}
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called()
            self.assertNotIn("127.0.0.1:1234", self.server.login_users)

    def test_handle_unknown_action(self):
        self.server.use_json = True
        with patch.object(JSONProtocol, 'receive', side_effect=[{"action": "unknown_action"}, None]), \
             patch.object(JSONProtocol, 'send') as mock_send:
            
            self.server.handle_client(self.mock_client_socket)
            mock_send.assert_called_with(self.mock_client_socket, {"status": "error", "message": "Unknown action"})

    def test_server_start(self):
        with patch.object(self.server.server, 'accept', side_effect=[(self.mock_client_socket, ('127.0.0.1', 1234)), KeyboardInterrupt]), \
             patch('threading.Thread') as mock_thread:
            
            with self.assertRaises(KeyboardInterrupt):  
                self.server.start()
            mock_thread.assert_called()


if __name__ == "__main__":
    unittest.main()
