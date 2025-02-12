import unittest
import sqlite3
import bcrypt
from storage import Storage

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.storage = Storage(":memory:")  # Use in-memory database for testing

    def tearDown(self):
        self.storage.conn.close()

    def test_login_register_user_register_success(self):
        response = self.storage.login_register_user("testuser", "testpass")
        self.assertEqual(response["status"], "success")

    def test_login_register_user_login_success(self):
        self.storage.login_register_user("testuser", "testpass")
        response = self.storage.login_register_user("testuser", "testpass")
        self.assertEqual(response["status"], "success")

    def test_login_register_user_invalid_password(self):
        self.storage.login_register_user("testuser", "testpass")
        response = self.storage.login_register_user("testuser", "wrongpass")
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], "Invalid credentials")

    def test_list_accounts(self):
        self.storage.login_register_user("user1", "pass1")
        self.storage.login_register_user("user2", "pass2")
        response = self.storage.list_accounts(1)
        self.assertEqual(response["status"], "success")
        self.assertIn("user1", response["message"])
        self.assertIn("user2", response["message"])

    def test_send_message_success(self):
        self.storage.login_register_user("sender", "pass")
        self.storage.login_register_user("recipient", "pass")
        response = self.storage.send_message("sender", "recipient", "Hello")
        self.assertEqual(response["status"], "success")

    def test_send_message_fail_no_recipient(self):
        self.storage.login_register_user("sender", "pass")
        response = self.storage.send_message("sender", "recipient", "Hello")
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], "Recipient does not exist")

    def test_read_messages(self):
        self.storage.login_register_user("sender", "pass")
        self.storage.login_register_user("recipient", "pass")
        self.storage.send_message("sender", "recipient", "Hello")
        response = self.storage.read_messages("recipient", limit=1)
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response["messages"]), 1)
        self.assertEqual(response["messages"][0]["message"], "Hello")

    def test_delete_message_success(self):
        self.storage.login_register_user("sender", "pass")
        self.storage.login_register_user("recipient", "pass")
        self.storage.send_message("sender", "recipient", "Hello")
        message_id = int(self.storage.cursor.execute("SELECT id FROM messages").fetchone()[0])
        response = self.storage.delete_message("sender", "recipient", message_id)
        self.assertEqual(response["status"], "success")

    def test_delete_account_success(self):
        self.storage.login_register_user("testuser", "testpass")
        response = self.storage.delete_account("testuser", "testpass")
        self.assertEqual(response["status"], "success")

    def test_delete_account_invalid_password(self):
        self.storage.login_register_user("testuser", "testpass")
        response = self.storage.delete_account("testuser", "wrongpass")
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], "Invalid credentials")

if __name__ == "__main__":
    unittest.main()
