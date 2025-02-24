import pytest
import grpc
import threading
from unittest.mock import MagicMock, patch
import chat_pb2
from client import run
from argparse import Namespace

class MockResponse:
    def __init__(self, status="success", message="", usernames=None, messages=None):
        self.status = status
        self.message = message
        self.usernames = usernames or []
        self.messages = messages or []

class MockMessage:
    def __init__(self, id=1, sender="test_sender", message="test_message"):
        self.id = id
        self.sender = sender
        self.message = message

class MockStub:
    def __init__(self):
        self.login_called = False
        self.logout_called = False
        self.send_message_called = False
        self.read_messages_called = False
        self.list_accounts_called = False
        self.delete_message_called = False
        self.delete_account_called = False
        
    def Login(self, request):
        self.login_called = True
        return MockResponse()
        
    def Logout(self, request):
        self.logout_called = True
        return MockResponse()
        
    def SendMessage(self, request):
        self.send_message_called = True
        return MockResponse()
        
    def ReadMessages(self, request):
        self.read_messages_called = True
        return MockResponse(messages=[MockMessage()])
        
    def ListAccounts(self, request):
        self.list_accounts_called = True
        return MockResponse(usernames=["user1", "user2"])
        
    def DeleteMessage(self, request):
        self.delete_message_called = True
        return MockResponse()
        
    def DeleteAccount(self, request):
        self.delete_account_called = True
        return MockResponse()
        
    def ListenForMessages(self, request):
        yield MockMessage()

@pytest.fixture
def mock_stub():
    return MockStub()

@pytest.fixture
def mock_args():
    return Namespace(host='127.0.0.1', port=50051)

@pytest.fixture
def mock_input(monkeypatch):
    inputs = []
    def mock_input(_):
        if inputs:
            return inputs.pop(0)
        return "6" 
    monkeypatch.setattr('builtins.input', mock_input)
    return inputs

def test_login_success(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend(["testuser", "testpass", "6"])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    captured = capsys.readouterr()
    assert "Login successful!" in captured.out
    assert mock_stub.login_called

def test_list_accounts(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend(["testuser", "testpass", "1", "6"])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    captured = capsys.readouterr()
    assert "Accounts:" in captured.out
    assert mock_stub.list_accounts_called

def test_send_message(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend([
        "testuser", "testpass",  # Login
        "2",                     # Choose send message
        "recipient",             # Enter recipient
        "test message",          # Enter message
        "6"                      # Exit
    ])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    assert mock_stub.send_message_called

def test_read_messages(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend([
        "testuser", "testpass",  # Login
        "3",                     # Choose read messages
        "5",                     # Number of messages to read
        "6"                      # Exit
    ])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    captured = capsys.readouterr()
    assert mock_stub.read_messages_called
    assert "From test_sender: test_message" in captured.out

def test_delete_message(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend([
        "testuser", "testpass",  # Login
        "4",                     # Choose delete message
        "recipient",             # Enter recipient
        "6"                      # Exit
    ])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    assert mock_stub.delete_message_called

def test_delete_account(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend([
        "testuser", "testpass",  # Login
        "5",                     # Choose delete account
        "yes",                   # Confirm deletion
        "6"                      # Exit
    ])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    assert mock_stub.delete_account_called

def test_logout(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend([
        "testuser", "testpass",  # Login
        "6"                      # Choose logout/exit
    ])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    captured = capsys.readouterr()
    assert "Logged out successfully" in captured.out
    assert mock_stub.logout_called

def test_invalid_message_limit(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend([
        "testuser", "testpass",  # Login
        "3",                     # Choose read messages
        "15",                    # Invalid number of messages
        "5",                     # Valid number of messages
        "6"                      # Exit
    ])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    captured = capsys.readouterr()
    assert "Please enter a number between 0 and 10" in captured.out

def test_listen_for_messages(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend(["testuser", "testpass", "6"])
    
    def mock_thread_start():
        pass
    
    with patch('threading.Thread') as mock_thread:
        mock_thread.return_value.start = mock_thread_start
        with patch('grpc.insecure_channel'), \
             patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub):
            run(mock_args)
    
    captured = capsys.readouterr()
    assert "Login successful!" in captured.out
    assert mock_stub.login_called

def test_empty_credentials(mock_stub, mock_input, mock_args, capsys):
    mock_input.extend([
        "",                  # Empty username
        "testuser",          # Valid username
        "",                  # Empty password
        "testpass",          # Valid password
        "6"                  # Exit
    ])
    
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub), \
         patch('threading.Thread'):
        run(mock_args)
        
    captured = capsys.readouterr()
    assert mock_stub.login_called