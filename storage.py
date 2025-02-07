import sqlite3
import bcrypt

class Storage:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, sender TEXT, recipient TEXT, message TEXT)")
        self.conn.commit()

    def register_user(self, username, password):
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            self.conn.commit()
            return {"status": "success"}
        except:
            return {"status": "error", "message": "User already exists"}

    def login_user(self, username, password):
        self.cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        user = self.cursor.fetchone()
        if user and bcrypt.checkpw(password.encode(), user[0]):
            return {"status": "success"}
        return {"status": "error", "message": "Invalid credentials"}
