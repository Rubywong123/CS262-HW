import pytest
import grpc
import chat_pb2
import chat_pb2_grpc
from server import ChatService
from concurrent import futures
import threading
import time
from queue import Queue
import sqlite3
import os

class MockContext:
    """Mock gRPC context for testing"""
    def __init__(self):
        self.aborted = False
        self.abort_code = None
        self.abort_details = None

    def abort(self, code, details):
        self.aborted = True
        self.abort_code = code
        self.abort_details = details

@pytest.fixture
def service():
    """Create a ChatService instance for testing"""
    if os.path.exists("test_data.db"):
        os.remove("test_data.db")
    service = ChatService()
    yield service
    if os.path.exists("test_data.db"):
        os.remove("test_data.db")

@pytest.fixture
def context():
    """Create a mock gRPC context"""
    return MockContext()

def test_login(service, context):
    """Test Login functionality"""
    # Test successful login/registration
    request = chat_pb2.LoginRequest(username="testuser", password="password123")
    response = service.Login(request, context)
    assert response.status == "success"
    assert "testuser" in service.online_users

    # Test logging in again
    response = service.Login(request, context)
    assert response.status == "success"

def test_logout(service, context):
    """Test Logout functionality"""
    # First login
    login_request = chat_pb2.LoginRequest(username="testuser", password="password123")
    service.Login(login_request, context)

    # Test logout
    request = chat_pb2.LogoutRequest(username="testuser")
    response = service.Logout(request, context)
    assert response.status == "success"
    assert "testuser" not in service.online_users

def test_list_accounts(service, context):
    """Test ListAccounts functionality"""
    # Create some test users first
    users = ["user1", "user2", "user3"]
    for user in users:
        login_request = chat_pb2.LoginRequest(username=user, password="password123")
        service.Login(login_request, context)

    # Test listing accounts
    request = chat_pb2.ListAccountsRequest(page_num=1)
    response = service.ListAccounts(request, context)
    assert len(response.usernames) > 0
    assert all(user in response.usernames for user in users)

def test_send_message(service, context):
    """Test SendMessage functionality"""
    # Create sender and recipient
    service.Login(chat_pb2.LoginRequest(username="sender", password="pass"), context)
    service.Login(chat_pb2.LoginRequest(username="recipient", password="pass"), context)

    # Test sending message to online user
    request = chat_pb2.SendMessageRequest(
        username="sender",
        recipient="recipient",
        message="Hello!"
    )
    response = service.SendMessage(request, context)
    assert response.status == "success"

    # Test sending to non-existent user
    request = chat_pb2.SendMessageRequest(
        username="sender",
        recipient="nonexistent",
        message="Hello!"
    )
    response = service.SendMessage(request, context)
    assert response.status == "error"

def test_read_messages(service, context):
    """Test ReadMessages functionality"""
    # Setup users and send a message
    service.Login(chat_pb2.LoginRequest(username="sender", password="pass"), context)
    service.Login(chat_pb2.LoginRequest(username="recipient", password="pass"), context)
    
    service.SendMessage(
        chat_pb2.SendMessageRequest(
            username="sender",
            recipient="recipient",
            message="Test message"
        ),
        context
    )

    # Test reading messages
    request = chat_pb2.ReadMessagesRequest(username="recipient", limit=10)
    response = service.ReadMessages(request, context)
    assert response.status == "success"
    assert len(response.messages) > 0
    assert response.messages[0].message == "Test message"

def test_delete_message(service, context):
    """Test DeleteMessage functionality"""
    # Setup users and send a message
    service.Login(chat_pb2.LoginRequest(username="sender", password="pass"), context)
    service.Login(chat_pb2.LoginRequest(username="recipient", password="pass"), context)
    
    service.SendMessage(
        chat_pb2.SendMessageRequest(
            username="sender",
            recipient="recipient",
            message="Delete me"
        ),
        context
    )

    # Test deleting message
    request = chat_pb2.DeleteMessageRequest(username="sender", recipient="recipient")
    response = service.DeleteMessage(request, context)
    assert response.status == "success"

def test_delete_account(service, context):
    """Test DeleteAccount functionality"""
    # Create an account
    service.Login(chat_pb2.LoginRequest(username="testuser", password="pass"), context)

    # Test account deletion
    request = chat_pb2.DeleteAccountRequest(username="testuser", password="pass")
    response = service.DeleteAccount(request, context)
    assert response.status == "success"
    assert "testuser" not in service.online_users

def test_listen_for_messages(service, context):
    """Test ListenForMessages functionality"""
    # Setup sender and recipient
    service.Login(chat_pb2.LoginRequest(username="sender", password="pass"), context)
    service.Login(chat_pb2.LoginRequest(username="listener", password="pass"), context)

    # Create a list to store received messages
    received_messages = []

    # Create a thread to simulate listening for messages
    def listen_thread():
        request = chat_pb2.ListenForMessagesRequest(username="listener")
        try:
            for message in service.ListenForMessages(request, context):
                received_messages.append(message)
                break  # Break after receiving one message
        except Exception:
            pass

    # Start listening thread
    thread = threading.Thread(target=listen_thread)
    thread.daemon = True
    thread.start()

    # Wait a moment for the listener to start
    time.sleep(0.1)

    # Send a message
    service.SendMessage(
        chat_pb2.SendMessageRequest(
            username="sender",
            recipient="listener",
            message="Real-time message"
        ),
        context
    )

    # Wait a moment for message to be received
    time.sleep(0.1)

    # Verify message was received
    assert len(received_messages) > 0
    assert received_messages[0].message == "Real-time message"

def test_listen_for_messages_not_logged_in(service, context):
    """Test ListenForMessages with non-logged-in user"""
    request = chat_pb2.ListenForMessagesRequest(username="nonexistent")
    messages = service.ListenForMessages(request, context)
    
    # Should trigger context.abort()
    assert context.aborted
    assert context.abort_code == grpc.StatusCode.NOT_FOUND