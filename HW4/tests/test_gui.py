import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
import chat_pb2
import gui
import tkinter as tk


class TestChatGUI(unittest.TestCase):

    @patch("sys.argv", ["gui.py"])
    @patch("tkinter.Tk")
    @patch("gui.chat_pb2_grpc.ChatServiceStub")
    @patch("gui.grpc.insecure_channel")
    def test_login_success(self, mock_channel, mock_stub_class, mock_tk):
        mock_stub = MagicMock()
        mock_stub.Login.return_value = chat_pb2.Response(status="success")
        mock_stub_class.return_value = mock_stub

        root = MagicMock()
        mock_tk.return_value = root

        app = gui.ChatGUI(root, gui.parse_args())

        app.username_entry = MagicMock()
        app.password_entry = MagicMock()
        app.username_entry.get.return_value = "alice"
        app.password_entry.get.return_value = "pw"

        with patch("tkinter.messagebox.showinfo") as mock_info:
            app.login()
            mock_info.assert_called_with("Success", "Login successful!")

    @patch("sys.argv", ["gui.py"])
    @patch("tkinter.Tk")
    @patch("gui.chat_pb2_grpc.ChatServiceStub")
    @patch("gui.grpc.insecure_channel")
    def test_login_failure(self, mock_channel, mock_stub_class, mock_tk):
        mock_stub = MagicMock()
        mock_stub.Login.return_value = chat_pb2.Response(status="error", message="Invalid credentials")
        mock_stub_class.return_value = mock_stub

        root = MagicMock()
        mock_tk.return_value = root

        app = gui.ChatGUI(root, gui.parse_args())

        app.username_entry = MagicMock()
        app.password_entry = MagicMock()
        app.username_entry.get.return_value = "alice"
        app.password_entry.get.return_value = "wrongpw"

        with patch("tkinter.messagebox.showerror") as mock_error:
            app.login()
            mock_error.assert_called_with("Login Failed", "Invalid credentials")

    @patch("sys.argv", ["gui.py"])
    @patch("tkinter.Tk")
    @patch("gui.chat_pb2_grpc.ChatServiceStub")
    @patch("gui.grpc.insecure_channel")
    def test_send_message_success(self, mock_channel, mock_stub_class, mock_tk):
        mock_stub = MagicMock()
        mock_stub.SendMessage.return_value = chat_pb2.Response(status="success", message="Sent")
        mock_stub_class.return_value = mock_stub

        root = MagicMock()
        mock_tk.return_value = root

        app = gui.ChatGUI(root, gui.parse_args())
        app.stub = mock_stub
        app.username = "alice"

        app.recipient_entry = MagicMock()
        app.message_entry = MagicMock()
        app.recipient_entry.get.return_value = "bob"
        app.message_entry.get.return_value = "hi"

        with patch("tkinter.messagebox.showinfo") as mock_info:
            app.send_message()
            mock_info.assert_called_with("Message Status", "Sent")

    @patch("sys.argv", ["gui.py"])
    @patch("tkinter.Tk")
    @patch("gui.chat_pb2_grpc.ChatServiceStub")
    @patch("gui.grpc.insecure_channel")
    def test_read_messages_display(self, mock_channel, mock_stub_class, mock_tk):
        mock_stub = MagicMock()
        mock_stub.ReadMessages.return_value = chat_pb2.ReadMessagesResponse(
            status="success",
            messages=[
                chat_pb2.Message(id=1, sender="bob", message="yo"),
                chat_pb2.Message(id=2, sender="charlie", message="hey"),
            ]
        )
        mock_stub_class.return_value = mock_stub

        root = MagicMock()
        mock_tk.return_value = root

        app = gui.ChatGUI(root, gui.parse_args())
        app.stub = mock_stub
        app.username = "alice"
        app.chat_display = MagicMock()

        with patch("tkinter.simpledialog.askinteger", return_value=2):
            app.read_messages()

        # Check that messages are inserted into chat display
        insert_calls = app.chat_display.insert.call_args_list
        assert any("bob" in str(call) for call in insert_calls)
        assert any("charlie" in str(call) for call in insert_calls)

class TestChatGUIExtended(unittest.TestCase):
    @patch("sys.argv", ["gui.py"])
    @patch("tkinter.Tk")
    @patch("gui.chat_pb2_grpc.ChatServiceStub")
    @patch("gui.grpc.insecure_channel")
    def setUp(self, mock_channel, mock_stub_class, mock_tk):
        mock_stub = MagicMock()
        mock_stub_class.return_value = mock_stub

        root = MagicMock()
        mock_tk.return_value = root

        self.app = gui.ChatGUI(root, gui.parse_args())
        self.app.stub = mock_stub

    def test_login_empty_credentials(self):
        self.app.username_entry = MagicMock()
        self.app.password_entry = MagicMock()
        self.app.username_entry.get.return_value = ""
        self.app.password_entry.get.return_value = ""

        with patch("tkinter.messagebox.showerror") as mock_error:
            self.app.login()
            mock_error.assert_called_with("Error", "Username and password cannot be empty")

    def test_list_accounts(self):
        mock_response = chat_pb2.ListAccountsResponse(usernames=["alice", "bob", "charlie"])
        self.app.stub.ListAccounts.return_value = mock_response

        with patch("tkinter.messagebox.showinfo") as mock_info:
            self.app.list_accounts()
            mock_info.assert_called_with("Accounts", "alice\nbob\ncharlie")

    def test_logout_success(self):
        self.app.username = "alice"
        mock_response = chat_pb2.Response(status="success")
        self.app.stub.Logout.return_value = mock_response

        with patch.object(self.app, "show_login_window") as mock_show_login:
            self.app.logout()
            mock_show_login.assert_called_once()

    def test_logout_failure(self):
        self.app.username = "alice"
        mock_response = chat_pb2.Response(status="error", message="Logout failed")
        self.app.stub.Logout.return_value = mock_response

        with patch("tkinter.messagebox.showerror") as mock_error:
            self.app.logout()
            mock_error.assert_called_with("Error", "Logout failed")

    def test_send_message_placeholder_validation(self):
        self.app.recipient_entry = MagicMock()
        self.app.message_entry = MagicMock()
        
        self.app.recipient_entry.get.return_value = "Enter recipient"
        self.app.message_entry.get.return_value = "Enter message"

        with patch("tkinter.messagebox.showerror") as mock_error:
            self.app.send_message()
            mock_error.assert_called_with("Error", "Please enter a valid recipient and message.")

    def test_delete_account_cancel(self):
        with patch("tkinter.messagebox.askyesno", return_value=False):
            self.app.delete_account()
            self.app.stub.DeleteAccount.assert_not_called()

    def test_delete_account_success(self):
        self.app.username = "alice"
        self.app.password = "pw"
        mock_response = chat_pb2.Response(status="success")
        self.app.stub.DeleteAccount.return_value = mock_response

        with patch("tkinter.messagebox.askyesno", return_value=True), \
             patch.object(self.app, "show_login_window") as mock_show_login:
            self.app.delete_account()
            self.app.stub.DeleteAccount.assert_called_with(
                chat_pb2.DeleteAccountRequest(username="alice", password="pw")
            )
            mock_show_login.assert_called_once()

    def test_delete_message_cancel(self):
        with patch("tkinter.simpledialog.askstring", return_value=None):
            self.app.delete_message()
            self.app.stub.DeleteMessage.assert_not_called()

    def test_read_messages_no_limit(self):
        with patch("tkinter.simpledialog.askinteger", return_value=None):
            self.app.read_messages()
            self.app.stub.ReadMessages.assert_not_called()

    def test_handle_close(self):
        self.app.username = "alice"
        with patch.object(self.app.channel, "close"), \
             patch.object(self.app.root, "destroy"):
            self.app.handle_close()
            self.app.stub.Logout.assert_called_with(
                chat_pb2.LogoutRequest(username="alice")
            )


if __name__ == "__main__":
    unittest.main()
