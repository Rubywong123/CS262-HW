import sqlite3
import bcrypt

class Storage:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, recipient TEXT, message TEXT, status TEXT)")
        self.conn.commit()

    def login_register_user(self, username, password):
        self.cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        user = self.cursor.fetchone()
        if user:
            if bcrypt.checkpw(password.encode(), user[0]):
                return {"status": "success"}
            return {"status": "error", "message": "Invalid credentials"}
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        self.conn.commit()
        return {"status": "success"}

    def list_accounts(self, page_num):
        self.cursor.execute("SELECT username FROM users")
        return {"status": "success", "message": [row[0] for row in self.cursor.fetchall()]}

    def send_message(self, sender, recipient, message):
        self.cursor.execute("INSERT INTO messages (sender, recipient, message, status) VALUES (?, ?, ?, 'unread')", (sender, recipient, message))
        self.conn.commit()
        return {"status": "success"}

    def read_messages(self, username, limit):
        self.cursor.execute("SELECT id, sender, message FROM messages WHERE recipient=? AND status='unread' LIMIT ?", (username, limit))
        messages = [{"id": row[0], "sender": row[1], "message": row[2]} for row in self.cursor.fetchall()]
        return {"status": "success", "messages": messages}
