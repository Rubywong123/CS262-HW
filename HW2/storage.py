import sqlite3
import bcrypt

class Storage:
    def __init__(self, db_name):
        self.db_name = db_name
        self._initialize_db()

    def _initialize_db(self):
        """ Initialize the database schema. """
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, recipient TEXT, message TEXT, status TEXT)")
            conn.commit()

    def get_connection(self):
        """ Create a new database connection for every request. """
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def login_register_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user:
            if bcrypt.checkpw(password.encode(), user[0]):
                conn.close()
                return {"status": "success"}
            conn.close()
            return {"status": "error", "message": "Invalid credentials"}

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()

        return {"status": "success"}

    def list_accounts(self, page_num):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT username FROM users")
        usernames = [row[0] for row in cursor.fetchall()]

        conn.close()
        return {"status": "success", "message": usernames}

    def send_message(self, sender, recipient, message):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO messages (sender, recipient, message, status) VALUES (?, ?, ?, 'unread')",
                       (sender, recipient, message))
        conn.commit()
        conn.close()

        return {"status": "success"}

    def read_messages(self, username, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, sender, message FROM messages WHERE recipient=? AND status='unread' LIMIT ?", 
                    (username, limit))
        messages = [{"id": row[0], "sender": row[1], "message": row[2]} for row in cursor.fetchall()]
        
        # Mark messages as read
        if messages:
            cursor.executemany("UPDATE messages SET status='read' WHERE id=?", [(msg["id"],) for msg in messages])

        conn.commit()
        conn.close()

        return {"status": "success", "messages": messages}


    def delete_message(self, message_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM messages WHERE id=?", (message_id,))
        conn.commit()
        conn.close()

        return {"status": "success"}

    def delete_account(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode(), user[0]):
            conn.close()
            return {"status": "error", "message": "Invalid credentials"}

        cursor.execute("DELETE FROM users WHERE username=?", (username,))
        cursor.execute("DELETE FROM messages WHERE recipient=?", (username,))
        conn.commit()
        conn.close()

        return {"status": "success"}

