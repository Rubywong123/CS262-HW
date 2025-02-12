import unittest
from unittest.mock import MagicMock
import json
import struct
from protocol import JSONProtocol, CustomProtocol

class TestJSONProtocol(unittest.TestCase):
    def setUp(self):
        self.mock_socket = MagicMock()
    
    def test_send_json(self):
        data = {"action": "login", "username": "testuser", "password": "testpass"}
        message = json.dumps(data).encode('utf-8')
        message_length = len(message).to_bytes(4, byteorder='big')
        
        JSONProtocol.send(self.mock_socket, data)
        self.mock_socket.sendall.assert_called_once_with(message_length + message)
    
    def test_receive_json(self):
        data = {"status": "success", "message": "Login successful"}
        message = json.dumps(data).encode('utf-8')
        message_length = len(message).to_bytes(4, byteorder='big')
        
        self.mock_socket.recv.side_effect = [message_length, message]
        received_data = JSONProtocol.receive(self.mock_socket)
        self.assertEqual(received_data, data)

class TestCustomProtocol(unittest.TestCase):
    def setUp(self):
        self.mock_socket = MagicMock()

    def test_encode_length_prefixed_field_short(self):
        encoded = CustomProtocol.encode_length_prefixed_field("test")
        expected = struct.pack(">B", 4) + b"test"
        self.assertEqual(encoded, expected)
    
    def test_encode_length_prefixed_field_long(self):
        long_string = "a" * 300
        encoded = CustomProtocol.encode_length_prefixed_field(long_string)
        expected = struct.pack(">BI", 0, 300) + long_string.encode("utf-8")
        self.assertEqual(encoded, expected)
    
    def test_send_custom_protocol_login(self):
        CustomProtocol.send(self.mock_socket, 1, username="testuser", password="testpass")
        self.mock_socket.sendall.assert_called()
    
    def test_receive_custom_protocol_login(self):
        username = "testuser"
        password = "testpass"
        encoded_username = CustomProtocol.encode_length_prefixed_field(username)
        encoded_password = CustomProtocol.encode_length_prefixed_field(password)
        
        message = struct.pack(">BB", 1, 2) + encoded_username + encoded_password
        message_length = struct.pack(">I", len(message))
        
        self.mock_socket.recv.side_effect = [message_length, message]
        received_data = CustomProtocol.receive(self.mock_socket)
        
        self.assertEqual(received_data, {"action": "login", "username": "testuser", "password": "testpass"})
    
    def test_send_custom_protocol_send_message(self):
        CustomProtocol.send(self.mock_socket, 3, recipient="friend", message="Hello")
        self.mock_socket.sendall.assert_called()
    
    def test_receive_custom_protocol_send_message(self):
        recipient = "friend"
        message = "Hello"
        encoded_recipient = CustomProtocol.encode_length_prefixed_field(recipient)
        encoded_message = CustomProtocol.encode_length_prefixed_field(message)
        
        message = struct.pack(">BB", 3, 2) + encoded_recipient + encoded_message
        message_length = struct.pack(">I", len(message))
        
        self.mock_socket.recv.side_effect = [message_length, message]
        received_data = CustomProtocol.receive(self.mock_socket)
        
        self.assertEqual(received_data, {"action": "send_message", "recipient": "friend", "message": "Hello"})

if __name__ == "__main__":
    unittest.main()
