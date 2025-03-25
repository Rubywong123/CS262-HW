import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
import chat_pb2
import client


class TestClient(unittest.TestCase):

    @patch("sys.argv", ["client.py"])
    @patch("builtins.input", side_effect=["alice", "pw"])
    @patch("client.grpc.insecure_channel")
    def test_login_success(self, mock_channel, mock_input):
        stub = MagicMock()
        stub.Login.return_value = chat_pb2.Response(status="success", message="")
        stub.Logout.return_value = chat_pb2.Response(status="success")

        with patch("client.chat_pb2_grpc.ChatServiceStub", return_value=stub):
            with patch("threading.Thread"):
                # simulate login and exit immediately
                with patch("builtins.input", side_effect=["alice", "pw", "6"]):
                    client.run(client.parse_args())

        stub.Login.assert_called_once()

    @patch("sys.argv", ["client.py"])
    @patch("builtins.input", side_effect=["alice", "wrongpw"])
    @patch("client.grpc.insecure_channel")
    def test_login_failure(self, mock_channel, mock_input):
        stub = MagicMock()
        stub.Login.return_value = chat_pb2.Response(status="error", message="Invalid credentials")

        with patch("client.chat_pb2_grpc.ChatServiceStub", return_value=stub):
            with patch("threading.Thread"):
                client.run(client.parse_args())

        stub.Login.assert_called_once()

    @patch("sys.argv", ["client.py"])
    @patch("builtins.input", side_effect=["alice", "pw", "2", "bob", "hi!", "6"])
    @patch("client.grpc.insecure_channel")
    def test_send_message_flow(self, mock_channel, mock_input):
        stub = MagicMock()
        stub.Login.return_value = chat_pb2.Response(status="success")
        stub.SendMessage.return_value = chat_pb2.Response(status="success", message="sent")
        stub.Logout.return_value = chat_pb2.Response(status="success")

        with patch("client.chat_pb2_grpc.ChatServiceStub", return_value=stub):
            with patch("threading.Thread"):
                client.run(client.parse_args())

        stub.SendMessage.assert_called_once()
        args = stub.SendMessage.call_args[0][0]
        self.assertEqual(args.username, "alice")
        self.assertEqual(args.recipient, "bob")
        self.assertEqual(args.message, "hi!")

    @patch("sys.argv", ["client.py"])
    @patch("builtins.input", side_effect=["alice", "pw", "5", "yes", "6"])
    @patch("client.grpc.insecure_channel")
    def test_delete_account_flow(self, mock_channel, mock_input):
        stub = MagicMock()
        stub.Login.return_value = chat_pb2.Response(status="success")
        stub.DeleteAccount.return_value = chat_pb2.Response(status="success", message="Deleted")
        stub.Logout.return_value = chat_pb2.Response(status="success")

        with patch("client.chat_pb2_grpc.ChatServiceStub", return_value=stub):
            with patch("threading.Thread"):
                client.run(client.parse_args())

        stub.DeleteAccount.assert_called_once()
        stub.Logout.assert_called()

    @patch("sys.argv", ["client.py"])
    @patch("builtins.input", side_effect=["alice", "pw", "3", "1", "6"])
    @patch("client.grpc.insecure_channel")
    def test_read_messages_flow(self, mock_channel, mock_input):
        stub = MagicMock()
        stub.Login.return_value = chat_pb2.Response(status="success")
        stub.ReadMessages.return_value = chat_pb2.ReadMessagesResponse(
            status="success",
            messages=[
                chat_pb2.Message(id=1, sender="bob", message="yo"),
                chat_pb2.Message(id=2, sender="charlie", message="hey"),
            ]
        )
        stub.Logout.return_value = chat_pb2.Response(status="success")

        with patch("client.chat_pb2_grpc.ChatServiceStub", return_value=stub):
            with patch("threading.Thread"):
                client.run(client.parse_args())

        stub.ReadMessages.assert_called_once()
        args = stub.ReadMessages.call_args[0][0]
        self.assertEqual(args.username, "alice")
        self.assertEqual(args.limit, 1)


if __name__ == "__main__":
    unittest.main()
