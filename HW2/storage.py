import sqlite3
import bcrypt
import time
import threading

class Storage:
    def __init__(self, db_name):
        self.db_name = db_name
        self.local = threading.local()
        self.initialize_database()

    def get_connection(self):
        """Ensures each thread gets its own SQLite connection."""
        if not hasattr(self.local, "conn"):
            self.local.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn

    def initialize_database(self):
        """Creates tables if they do not exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash BLOB)")
        cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY, sender TEXT, recipient TEXT, message TEXT, status TEXT)")
        conn.commit()
        conn.close()

    def execute_query(self, query, params=(), commit=False):
        """Executes a query using a thread-local SQLite connection."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor

    def login_register_user(self, username, password):
        """Handles user login or registration."""
        cursor = self.execute_query("SELECT password_hash FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        if user:
            if bcrypt.checkpw(password.encode(), user[0]):
                return {"status": "success"}
            return {"status": "error", "message": "Invalid credentials"}
        else:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            self.execute_query("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash), commit=True)
            return {"status": "success"}

    def list_accounts(self, page_num):
        """Lists users with pagination."""
        num_per_page = 5
        offset = (page_num - 1) * num_per_page
        cursor = self.execute_query("SELECT username FROM users ORDER BY username LIMIT ? OFFSET ?", (num_per_page, offset))
        return {
            'status': 'success',
            'message': [row[0] for row in cursor.fetchall()]
        }

    def send_message(self, sender, recipient, message, status='unread'):
        """Stores a message in the database."""
        cursor = self.execute_query("SELECT username FROM users WHERE username=?", (recipient,))
        if not cursor.fetchone():
            return {"status": "error", "message": "Recipient does not exist"}
        
        message_id = int(time.time())
        self.execute_query("INSERT INTO messages (id, sender, recipient, message, status) VALUES (?, ?, ?, ?, ?)",
                           (message_id, sender, recipient, message, status), commit=True)
        return {"status": "success"}

    def read_messages(self, username, limit=10):
        """Retrieves unread messages for a user within the specified limit (0-10)."""
        limit = max(0, min(limit, 10))

        if limit == 0:
            return {"status": "success", "messages": []}

        cursor = self.execute_query("""
            SELECT id, sender, recipient, message 
            FROM messages 
            WHERE recipient=? 
            AND status='unread' 
            AND sender != ? 
            ORDER BY id DESC LIMIT ?
        """, (username, username, limit))
        
        messages = [{"id": row["id"], "sender": row["sender"], "message": row["message"]} for row in cursor.fetchall()]

        if messages:
            for message in messages:
                self.execute_query("UPDATE messages SET status='read' WHERE id=?", (message["id"],), commit=True)

        return {"status": "success", "messages": messages}


    def delete_message(self, username, recipient, message_id):
        """Deletes a message if the sender is the current user."""
        try:
            self.execute_query("DELETE FROM messages WHERE id=? AND sender=? AND recipient=?", 
                               (int(message_id), username, recipient), commit=True)
            return {"status": "success"}
        except sqlite3.IntegrityError:
            return {"status": "error", "message": "Message not found or you are not the sender"}
        

    def delete_account(self, username, password):
        """Deletes a user account if the credentials match."""
        try:
            cursor = self.execute_query("SELECT password_hash FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            if not user or not bcrypt.checkpw(password.encode(), user[0]):
                return {"status": "error", "message": "Invalid credentials"}

            # Delete the user and their messages
            self.execute_query("DELETE FROM users WHERE username=?", (username,), commit=True)
            self.execute_query("DELETE FROM messages WHERE recipient=?", (username,), commit=True)

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
