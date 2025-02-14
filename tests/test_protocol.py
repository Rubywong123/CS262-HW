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

    def test_receive_empty_json(self):
        """Test receiving empty data."""
        self.mock_socket.recv.side_effect = [b"", b""]
        received_data = JSONProtocol.receive(self.mock_socket)
        self.assertIsNone(received_data)

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

    def test_send_custom_protocol_list_accounts(self):
        """Test sending a request to list accounts (page_num)."""
        CustomProtocol.send(self.mock_socket, 2, page_num=3)
        self.mock_socket.sendall.assert_called()

    def test_receive_custom_protocol_list_accounts(self):
        """Test receiving a response for listing accounts."""
        message = struct.pack(">BB", 2, 1) + struct.pack(">B", 3)
        message_length = struct.pack(">I", len(message))
        
        self.mock_socket.recv.side_effect = [message_length, message]
        received_data = CustomProtocol.receive(self.mock_socket)
        
        self.assertEqual(received_data, {"action": "list_accounts", "page_num": 3})

    def test_send_custom_protocol_delete_message(self):
        """Test sending a delete message request."""
        CustomProtocol.send(self.mock_socket, 5, recipient="friend", message_id=12345)
        self.mock_socket.sendall.assert_called()

    def test_receive_custom_protocol_delete_message(self):
        """Test receiving a delete message request."""
        recipient = "friend"
        message_id = 12345
        encoded_recipient = CustomProtocol.encode_length_prefixed_field(recipient)
        encoded_message_id = struct.pack(">I", message_id)
        
        message = struct.pack(">BB", 5, 2) + encoded_recipient + encoded_message_id
        message_length = struct.pack(">I", len(message))
        
        self.mock_socket.recv.side_effect = [message_length, message]
        received_data = CustomProtocol.receive(self.mock_socket)
        
        self.assertEqual(received_data, {"action": "delete_message", "recipient": "friend", "message_id": 12345})

    def test_send_custom_protocol_response(self):
        """Test sending a response message."""
        CustomProtocol.send(self.mock_socket, 7, status="success", message="Action completed")
        self.mock_socket.sendall.assert_called()

    def test_receive_custom_protocol_response(self):
        """Test receiving a response message."""
        status = "success"
        message = "Action completed"
        encoded_status = CustomProtocol.encode_length_prefixed_field(status)
        encoded_message = CustomProtocol.encode_length_prefixed_field(message)
        
        message = struct.pack(">BB", 7, 2) + encoded_status + encoded_message
        message_length = struct.pack(">I", len(message))
        
        self.mock_socket.recv.side_effect = [message_length, message]
        received_data = CustomProtocol.receive(self.mock_socket)
        
        self.assertEqual(received_data, {"action": "response", "status": "success", "message": "Action completed"})

    def test_extract_field_short(self):
        """Test extracting a short field (1-byte length)."""
        data = struct.pack(">B", 4) + b"test"
        value, size = CustomProtocol._extract_field(data, 0)
        self.assertEqual(value, "test")
        self.assertEqual(size, 5)

    def test_extract_field_long(self):
        """Test extracting a long field (4-byte length)."""
        long_string = "a" * 300
        data = struct.pack(">BI", 0, 300) + long_string.encode("utf-8")
        value, size = CustomProtocol._extract_field(data, 0)
        self.assertEqual(value, long_string)
        self.assertEqual(size, 305)

    def test_receive_empty_message(self):
        """Test receiving an empty message."""
        self.mock_socket.recv.side_effect = [b"", b""]
        received_data = CustomProtocol.receive(self.mock_socket)
        self.assertIsNone(received_data)

if __name__ == "__main__":
    unittest.main()
