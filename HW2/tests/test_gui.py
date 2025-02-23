import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
import grpc
import chat_pb2
from gui import ChatGUI

class MockResponse:
    """Mock gRPC response object"""
    def __init__(self, status="success", message="", usernames=None, messages=None):
        self.status = status
        self.message = message
        self.usernames = usernames or []
        self.messages = messages or []

class MockMessage:
    """Mock message object for streaming"""
    def __init__(self, id=1, sender="test_sender", message="test_message"):
        self.id = id
        self.sender = sender
        self.message = message

class MockStub:
    """Mock gRPC stub with tracking of method calls"""
    def __init__(self):
        self.login_called = False
        self.logout_called = False
        self.send_message_called = False
        self.read_messages_called = False
        self.list_accounts_called = False
        self.delete_message_called = False
        self.delete_account_called = False
        self.listen_called = False
        
        self.read_messages_response = None
        
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
        if self.read_messages_response:
            return self.read_messages_response
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
        self.listen_called = True
        yield MockMessage()

@pytest.fixture
def root():
    """Fixture for tkinter root window"""
    root = tk.Tk()
    yield root
    root.destroy()

@pytest.fixture
def mock_stub():
    """Fixture for mock gRPC stub"""
    return MockStub()

@pytest.fixture
def chat_gui(root, mock_stub):
    """Fixture for ChatGUI instance"""
    with patch('grpc.insecure_channel'), \
         patch('chat_pb2_grpc.ChatServiceStub', return_value=mock_stub):
        gui = ChatGUI(root)
        root.update()
        yield gui

def test_initial_state(chat_gui):
    """Test initial state of GUI elements"""
    assert chat_gui.username is None
    assert chat_gui.password is None
    assert hasattr(chat_gui, 'username_entry')
    assert hasattr(chat_gui, 'password_entry')

def test_login_success(chat_gui, mock_stub):
    """Test successful login"""
    chat_gui.username_entry.insert(0, "testuser")
    chat_gui.password_entry.insert(0, "testpass")
    
    with patch('tkinter.messagebox.showinfo') as mock_info:
        chat_gui.login()
        
    assert chat_gui.username == "testuser"
    assert chat_gui.password == "testpass"
    assert mock_stub.login_called
    mock_info.assert_called_once_with("Success", "Login successful!")

def test_login_empty_fields(chat_gui):
    """Test login with empty fields"""
    with patch('tkinter.messagebox.showerror') as mock_error:
        chat_gui.login()
        
    mock_error.assert_called_once_with("Error", "Username and password cannot be empty")

def test_send_message_success(chat_gui, mock_stub):
    """Test sending a message"""
    chat_gui.username = "testuser"
    chat_gui.show_chat_window() 
    
    chat_gui.recipient_entry.delete(0, tk.END)
    chat_gui.recipient_entry.insert(0, "recipient")
    chat_gui.message_entry.delete(0, tk.END)
    chat_gui.message_entry.insert(0, "test message")
    
    with patch('tkinter.messagebox.showinfo') as mock_info:
        chat_gui.send_message()
        
    assert mock_stub.send_message_called
    mock_info.assert_called_once()

def test_read_messages(chat_gui, mock_stub):
    """Test reading messages"""
    chat_gui.username = "testuser"
    chat_gui.show_chat_window()
    
    mock_messages = [
        MockMessage(sender="user1", message="message1"),
        MockMessage(sender="user2", message="message2")
    ]
    
    mock_stub.read_messages_response = MockResponse(messages=mock_messages)
    with patch('tkinter.simpledialog.askinteger', return_value=2):
        chat_gui.read_messages()
    assert mock_stub.read_messages_called

    display_text = chat_gui.chat_display.get("1.0", tk.END)
    expected_text = "\n--- Messages ---\nFrom user1: message1\nFrom user2: message2\n"
    assert expected_text.strip() in display_text.strip()

def test_list_accounts(chat_gui, mock_stub):
    """Test listing accounts"""
    mock_stub.list_accounts_response = MockResponse(usernames=["user1", "user2"])
    
    with patch('tkinter.messagebox.showinfo') as mock_info:
        chat_gui.list_accounts()
        
    assert mock_stub.list_accounts_called
    mock_info.assert_called_once_with("Accounts", "user1\nuser2")

def test_delete_message(chat_gui, mock_stub):
    """Test deleting a message"""
    chat_gui.username = "testuser"
    
    with patch('tkinter.simpledialog.askstring', return_value="recipient"), \
         patch('tkinter.messagebox.showinfo') as mock_info:
        chat_gui.delete_message()
        
    assert mock_stub.delete_message_called
    mock_info.assert_called_once()

def test_delete_account_confirmed(chat_gui, mock_stub):
    """Test deleting account with confirmation"""
    chat_gui.username = "testuser"
    chat_gui.password = "testpass"
    
    with patch('tkinter.messagebox.askyesno', return_value=True), \
         patch('tkinter.messagebox.showinfo') as mock_info:
        chat_gui.delete_account()
        
    assert mock_stub.delete_account_called
    mock_info.assert_called_once()

def test_delete_account_cancelled(chat_gui, mock_stub):
    """Test cancelling account deletion"""
    chat_gui.username = "testuser"
    
    with patch('tkinter.messagebox.askyesno', return_value=False):
        chat_gui.delete_account()
        
    assert not mock_stub.delete_account_called

def test_logout(chat_gui, mock_stub):
    """Test logout functionality"""
    chat_gui.username = "testuser"
    chat_gui.show_chat_window()  # Show chat window first
    
    with patch('tkinter.messagebox.showinfo') as mock_info:
        chat_gui.logout()
        
    assert mock_stub.logout_called
    # Check if we're back to login window
    assert any(isinstance(widget, tk.Entry) for widget in chat_gui.root.winfo_children())

def test_handle_close(chat_gui, mock_stub):
    """Test window close handling"""
    chat_gui.username = "testuser"
    
    with patch.object(chat_gui.root, 'destroy') as mock_destroy, \
         patch.object(chat_gui.channel, 'close') as mock_close:
        chat_gui.handle_close()
        
    assert mock_stub.logout_called
    mock_destroy.assert_called_once()
    mock_close.assert_called_once()

def test_display_message(chat_gui):
    """Test message display functionality"""
    chat_gui.username = "testuser"
    chat_gui.show_chat_window()  # Show chat window first
    
    test_message = "Test message"
    chat_gui.display_message(test_message)
    
    display_text = chat_gui.chat_display.get("1.0", tk.END)
    assert test_message in display_text.strip()


