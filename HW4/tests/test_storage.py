import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import os
import tempfile
from storage import Storage
import bcrypt
import time
import chat_pb2  # Required for store_synced_data test

class TestStorage(unittest.TestCase):
    def setUp(self):
        # Create a temporary SQLite DB
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.storage = Storage(self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.remove(self.db_path)

    def test_login_register_user(self):
        result = self.storage.login_register_user("alice", "secret")
        self.assertEqual(result["status"], "success")

        result = self.storage.login_register_user("alice", "secret")
        self.assertEqual(result["status"], "success")

        result = self.storage.login_register_user("alice", "wrong")
        self.assertEqual(result["status"], "error")

    def test_send_message_success_and_failure(self):
        self.storage.login_register_user("alice", "pw")
        self.storage.login_register_user("bob", "pw")
        result = self.storage.send_message("alice", "bob", "hi bob")
        self.assertEqual(result["status"], "success")

        result = self.storage.send_message("alice", "charlie", "hi?")
        self.assertEqual(result["status"], "error")

    def test_read_messages(self):
        self.storage.login_register_user("alice", "pw")
        self.storage.login_register_user("bob", "pw")

        self.storage.send_message("bob", "alice", "hey alice")
        result = self.storage.read_messages("alice", limit=1)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["messages"]), 1)

        result = self.storage.read_messages("alice", limit=1)
        self.assertEqual(result["status"], "error")

    def test_delete_message(self):
        self.storage.login_register_user("alice", "pw")
        self.storage.login_register_user("bob", "pw")

        self.storage.send_message("alice", "bob", "msg 1")
        result = self.storage.delete_message("alice", "bob")
        self.assertEqual(result["status"], "success")

        with self.assertRaises(TypeError) as context:
            self.storage.delete_message("alice", "bob")
        
        self.assertIn("subscriptable", str(context.exception))


    def test_delete_account_success_and_fail(self):
        self.storage.login_register_user("alice", "pw")
        result = self.storage.delete_account("alice", "pw")
        self.assertEqual(result["status"], "success")

        result = self.storage.delete_account("alice", "wrong")
        self.assertEqual(result["status"], "error")

    def test_get_all_users_and_messages(self):
        self.storage.login_register_user("alice", "pw")
        self.storage.login_register_user("bob", "pw")
        self.storage.send_message("alice", "bob", "test msg")

        users = self.storage.get_all_users()
        self.assertEqual(len(users), 2)

        messages = self.storage.get_all_messages()
        self.assertEqual(len(messages), 1)

    def test_store_synced_data(self):
        msg = chat_pb2.MessageData(
            id=123,
            sender="alice",
            recipient="bob",
            message="hello",
            status="read"
        )
        user = chat_pb2.UserData(
            username="alice",
            password_hash=bcrypt.hashpw(b"pw", bcrypt.gensalt())
        )

        result = self.storage.store_synced_data([msg], [user])
        self.assertEqual(result["status"], "success")

        self.assertEqual(len(self.storage.get_all_users()), 1)
        self.assertEqual(len(self.storage.get_all_messages()), 1)

if __name__ == "__main__":
    unittest.main()
