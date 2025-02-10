import sqlite3
import bcrypt
import time

class Storage:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, sender TEXT, recipient TEXT, message TEXT)")
        self.conn.commit()

    def login_register_user(self, username, password):

        # find if the username exists
        self.cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        user = self.cursor.fetchone()
        if user:
            # do the login process
            if bcrypt.checkpw(password.encode(), user[0]):
                return {"status": "success"}
            
            return {"status": "error", "message": "Invalid credentials"}
        else:
            # do the register process
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            self.conn.commit()
            return {"status": "success"}
    
    def list_accounts(self):
        self.cursor.execute("SELECT username FROM users")
        return [row[0] for row in self.cursor.fetchall()]
    
    def send_message(self, sender, recipient, message):

        # check if sender and recipient exist
        self.cursor.execute("SELECT username FROM users WHERE username=?", (sender,))
        if not self.cursor.fetchone():
            return {"status": "error", "message": "Sender does not exist"}
        self.cursor.execute("SELECT username FROM users WHERE username=?", (recipient,))
        if not self.cursor.fetchone():
            return {"status": "error", "message": "Recipient does not exist"}
        
        id = time.time()
        id = f'{sender}-{recipient}-{id}'
        self.cursor.execute("INSERT INTO messages (id, sender, recipient, message, status) VALUES (?, ?, ?, ?, 'unread')", (id, sender, recipient, message))
        self.conn.commit()
        return {"status": "success"}
    
    def read_messages(self, username, limit=10):
        # read undelivered messages
        self.cursor.execute("SELECT id, sender, message FROM messages WHERE sender=? and status='unread' ORDER BY id DESC LIMIT ?", (username, limit))
        messages = [{"id": row[0], "sender": row[1], "message": row[2]} for row in self.cursor.fetchall()]
        # mark messages as read
        for message in messages:
            self.cursor.execute("UPDATE messages SET status='read' WHERE id=?", (message["id"],))

        self.conn.commit()
        return messages
    
    def delete_message(self, username, message_id):
        self.cursor.execute("DELETE FROM messages WHERE id=? AND sender=?", (message_id, username))
        self.conn.commit()
        return {"status": "success"}
    
    def delete_account(self, username, password):
        # delete the account
        self.cursor.execute("DELETE FROM users WHERE username=? AND password_hash=?", (username, bcrypt.hashpw(password.encode(), bcrypt.gensalt())))
        self.conn.commit()
        # delete all messages that sending to the account
        self.cursor.execute("DELETE FROM messages WHERE recipient=?", (username,))
        self.conn.commit()
        return {"status": "success"}
        
