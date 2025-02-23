import pytest
import sqlite3
import bcrypt
from storage import Storage
import os
import time

@pytest.fixture
def storage():
    """Create a temporary test database."""
    test_db = "test_data.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    storage = Storage(test_db)
    yield storage
    if os.path.exists(test_db):
        os.remove(test_db)

def test_initialize_database(storage):
    """Test if database is properly initialized with required tables."""
    conn = sqlite3.connect(storage.db_name)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {table[0] for table in cursor.fetchall()}
    
    assert "users" in tables
    assert "messages" in tables
    
    cursor.execute("PRAGMA table_info(users)")
    user_columns = {col[1] for col in cursor.fetchall()}
    assert "username" in user_columns
    assert "password_hash" in user_columns
    
    cursor.execute("PRAGMA table_info(messages)")
    message_columns = {col[1] for col in cursor.fetchall()}
    assert all(col in message_columns for col in ["id", "sender", "recipient", "message", "status"])
    
    conn.close()

def test_login_register_user(storage):
    """Test user registration and login functionality."""
    # test registration
    result = storage.login_register_user("testuser", "password123")
    assert result["status"] == "success"
    
    # test login with correct password
    result = storage.login_register_user("testuser", "password123")
    assert result["status"] == "success"
    
    # test login with incorrect password
    result = storage.login_register_user("testuser", "wrongpassword")
    assert result["status"] == "error"
    assert result["message"] == "Invalid credentials"

def test_list_accounts(storage):
    """Test account listing with pagination."""
    test_users = ["user1", "user2", "user3", "user4", "user5", "user6"]
    for user in test_users:
        storage.login_register_user(user, "password123")
    
    # test first page
    result = storage.list_accounts(1)
    assert result["status"] == "success"
    assert len(result["message"]) <= 5
    
    # test second page
    result = storage.list_accounts(2)
    assert result["status"] == "success"
    assert len(result["message"]) <= 5

def test_send_message(storage):
    """Test message sending functionality."""
    storage.login_register_user("sender", "password123")
    storage.login_register_user("recipient", "password123")
    
    # test sending valid message
    result = storage.send_message("sender", "recipient", "Hello!")
    assert result["status"] == "success"
    
    # test sending to non-existent user
    result = storage.send_message("sender", "nonexistent", "Hello!")
    assert result["status"] == "error"
    assert "Recipient does not exist" in result["message"]

def test_read_messages(storage):
    """Test message reading functionality."""
    storage.login_register_user("sender", "password123")
    storage.login_register_user("recipient", "password123")
    
    storage.execute_query(
        "INSERT INTO messages (id, sender, recipient, message, status) VALUES (?, ?, ?, ?, ?)",
        (1, "sender", "recipient", "Message 1", "unread"),
        commit=True
    )
    storage.execute_query(
        "INSERT INTO messages (id, sender, recipient, message, status) VALUES (?, ?, ?, ?, ?)",
        (2, "sender", "recipient", "Message 2", "unread"),
        commit=True
    )
    
    # test reading messages
    result = storage.read_messages("recipient", limit=2)
    assert result["status"] == "success"
    assert len(result["messages"]) == 2
    
    # test reading messages after they're marked as read
    result = storage.read_messages("recipient", limit=2)
    assert result["status"] == "error"
    assert result["messages"][0]["message"] == "No unread messages from other users"

def test_delete_message(storage):
    """Test message deletion functionality."""
    storage.login_register_user("sender", "password123")
    storage.login_register_user("recipient", "password123")
    
    storage.execute_query(
        "INSERT INTO messages (id, sender, recipient, message, status) VALUES (?, ?, ?, ?, ?)",
        (1, "sender", "recipient", "Delete me", "unread"),
        commit=True
    )
    
    # test delete message when it exists
    try:
        result = storage.delete_message("sender", "recipient")
        assert result["status"] == "success"
        
        # Verify message was deleted
        cursor = storage.execute_query("SELECT * FROM messages WHERE id=1")
        assert cursor.fetchone() is None
    except Exception as e:
        pytest.fail(f"Failed to delete existing message: {str(e)}")

    try:
        result = storage.delete_message("sender", "recipient")
        assert result["status"] == "error"
    except TypeError:
        pass

def test_delete_account(storage):
    """Test account deletion functionality."""
    # Create test user
    storage.login_register_user("testuser", "password123")
    
    result = storage.delete_account("testuser", "password123")
    assert result["status"] == "success"
    
    result = storage.delete_account("testuser", "password123")
    assert result["status"] == "error"
    
    storage.login_register_user("testuser2", "password123")
    result = storage.delete_account("testuser2", "wrongpassword")
    assert result["status"] == "error"
    assert "Invalid credentials" in result["message"]

def test_thread_safety(storage):
    """Test thread-local connections."""
    import threading
    
    def thread_operation(storage, results):
        try:
            storage.login_register_user(f"thread_user_{threading.get_ident()}", "password123")
            results.append(True)
        except Exception as e:
            results.append(False)
    
    results = []
    threads = []
    
    for _ in range(5):
        thread = threading.Thread(target=thread_operation, args=(storage, results))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert all(results)