import sqlite3
import bcrypt
import time

class Storage:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY, sender TEXT, recipient TEXT, message TEXT, status TEXT)")
        self.conn.commit()

    def login_register_user(self, username, password):
        
        # change it to bytes type
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
    
    def list_accounts(self, page_num):
        num_per_page = 5
        
        offset = (page_num - 1) * num_per_page

        self.cursor.execute("SELECT username FROM users ORDER BY username LIMIT ? OFFSET ?", (num_per_page, offset))
        response = {
            'status': 'success',
            'message': [row[0] for row in self.cursor.fetchall()]
        }
        return response
    
    def send_message(self, sender, recipient, message):

        # check if recipient exist
        self.cursor.execute("SELECT username FROM users WHERE username=?", (recipient,))
        if not self.cursor.fetchone():
            return {"status": "error", "message": "Recipient does not exist"}
        
        id = int(time.time())
        
        self.cursor.execute("INSERT INTO messages (id, sender, recipient, message, status) VALUES (?, ?, ?, ?, 'unread')", (id, sender, recipient, message))
        self.conn.commit()
        return {"status": "success"}
    
    # def read_messages(self, username, limit=10):
    #     # read undelivered messages
    #     self.cursor.execute("SELECT id, sender, recipient, message FROM messages WHERE recipient=? and status='unread' ORDER BY id DESC LIMIT ?", (username, limit))
        
    #     messages = [{"id": row[0], "sender": row[1], "message": row[3]} for row in self.cursor.fetchall()]
        
    #     # mark messages as read
    #     for message in messages:
    #         self.cursor.execute("UPDATE messages SET status='read' WHERE id=?", (message["id"],))

    #     self.conn.commit()

    #     # if no undelivered messages, return a response

    #     if messages:
    #         response = {
    #             'status': 'success',
    #             'messages': messages
    #         }
    #     else:
    #         response = {
    #             'status': 'error',
    #             'messages': 'No messages unread'
    #         }

    #     return response

    def read_messages(self, username, limit=10):
        # read undelivered messages from other senders only
        self.cursor.execute("""
            SELECT id, sender, recipient, message 
            FROM messages 
            WHERE recipient=? 
            AND status='unread' 
            AND sender != ? 
            ORDER BY id DESC LIMIT ?
        """, (username, username, limit))
        
        messages = [{"id": row[0], "sender": row[1], "message": row[3]} for row in self.cursor.fetchall()]
        
        # mark messages as read
        for message in messages:
            self.cursor.execute("UPDATE messages SET status='read' WHERE id=?", (message["id"],))

        self.conn.commit()

        # if no undelivered messages, return a response
        if messages:
            response = {
                'status': 'success',
                'messages': messages
            }
        else:
            response = {
                'status': 'error',
                'messages': 'No unread messages from other users'
            }

        return response
        
    def delete_message(self, username, recipient, message_id: str):
        self.cursor.execute("DELETE FROM messages WHERE id=? AND sender=? AND recipient=?", (int(message_id), username, recipient))
        self.conn.commit()
        return {"status": "success"}
    
    def delete_account(self, username, password):
        
        # check if the password is correct
        self.cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        user = self.cursor.fetchone()
        if not bcrypt.checkpw(password.encode(), user[0]):
            return {"status": "error", "message": "Invalid credentials"}

        # delete the account
        self.cursor.execute("DELETE FROM users WHERE username=?", (username,))
        self.conn.commit()
        # delete all messages that sending to the account
        self.cursor.execute("DELETE FROM messages WHERE recipient=?", (username,))
        self.conn.commit()
        return {"status": "success"}
        