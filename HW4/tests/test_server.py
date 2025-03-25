import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock, patch
import chat_pb2
import chat_pb2_grpc
from server import ChatService,get_local_ip
from storage import Storage
import queue
import grpc

class TestChatService(unittest.TestCase):
    def setUp(self):
        patcher = patch('server.Storage', autospec=True)
        self.MockStorage = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_storage = self.MockStorage.return_value
        self.chat_service = ChatService(
            port=50052,
            is_leader=True,
            leader_address=None,
            replica_addresses=[]
        )
    
    def test_login_register_success(self):
        self.mock_storage.login_register_user.return_value = {"status": "success"}
        request = chat_pb2.LoginRequest(username="alice", password="secret")
        response = self.chat_service.Login(request, None)

        self.assertEqual(response.status, "success")
        self.assertIn("alice", self.chat_service.online_users)

    def test_login_invalid_credentials(self):
        self.mock_storage.login_register_user.return_value = {
            "status": "error",
            "message": "Invalid credentials"
        }
        request = chat_pb2.LoginRequest(username="bob", password="wrong")
        response = self.chat_service.Login(request, None)

        self.assertEqual(response.status, "error")
        self.assertNotIn("bob", self.chat_service.online_users)

    def test_send_message_success(self):
        self.chat_service.online_users = {"bob": queue.Queue()}
        self.mock_storage.send_message.return_value = {"status": "success"}

        request = chat_pb2.SendMessageRequest(username="alice", recipient="bob", message="hello!")
        response = self.chat_service.SendMessage(request, None)

        self.assertEqual(response.status, "success")
        self.assertIn("delivered", response.message)

    def test_send_message_fails_if_not_leader(self):
        self.chat_service.is_leader = False
        request = chat_pb2.SendMessageRequest(username="alice", recipient="bob", message="hey!")
        response = self.chat_service.SendMessage(request, None)

        self.assertEqual(response.status, "error")
        self.assertIn("Not the leader", response.message)

    def test_read_messages_success(self):
        self.chat_service.is_leader = False  # Simulate follower
        self.mock_storage.read_messages.return_value = {
            "status": "success",
            "messages": [
                {"id": 1, "sender": "alice", "message": "hello"}
            ]
        }

        request = chat_pb2.ReadMessagesRequest(username="bob", limit=1)
        response = self.chat_service.ReadMessages(request, None)

        self.assertEqual(response.status, "success")
        self.assertEqual(len(response.messages), 1)
        self.assertEqual(response.messages[0].sender, "alice")

    def test_delete_account_success(self):
        self.mock_storage.delete_account.return_value = {"status": "success", "message": "Deleted"}
        request = chat_pb2.DeleteAccountRequest(username="alice", password="secret")
        response = self.chat_service.DeleteAccount(request, None)

        self.assertEqual(response.status, "success")

    def test_heartbeat_response(self):
        response = self.chat_service.Heartbeat(chat_pb2.HeartbeatRequest(), None)
        self.assertEqual(response.status, "alive")

    def test_who_is_leader_as_leader(self):
        response = self.chat_service.WhoIsLeader(None, None)
        self.assertTrue(response.is_leader)
        self.assertIn("50052", response.leader_address)

    def test_sync_data_returns_data(self):
        self.mock_storage.get_all_messages.return_value = [
            {"id": 1, "sender": "alice", "recipient": "bob", "message": "hi", "status": "read"}
        ]
        self.mock_storage.get_all_users.return_value = [
            {"username": "alice", "password_hash": b"hash"}
        ]
        self.chat_service.online_users = {"alice": MagicMock()}
        request = chat_pb2.SyncDataRequest(replica_address="127.0.0.1:50053")

        response = self.chat_service.SyncData(request, None)
        self.assertEqual(response.status, "success")
        self.assertEqual(len(response.messages), 1)
        self.assertEqual(len(response.users), 1)


    def test_delete_message_success(self):
        self.mock_storage.delete_message.return_value = {"status": "success", "message": "Deleted"}
        request = chat_pb2.DeleteMessageRequest(username="alice", recipient="bob")
        response = self.chat_service.DeleteMessage(request, None)
        self.assertEqual(response.status, "success")

    def test_logout(self):
        self.chat_service.online_users = {"alice": queue.Queue()}
        request = chat_pb2.LogoutRequest(username="alice")
        response = self.chat_service.Logout(request, None)
        self.assertEqual(response.status, "success")
        self.assertNotIn("alice", self.chat_service.online_users)

    def test_list_accounts_as_follower(self):
        self.chat_service.is_leader = False
        self.mock_storage.list_accounts.return_value = {
            "status": "success",
            "usernames": ["alice", "bob"]
        }

        request = chat_pb2.ListAccountsRequest(page_num=1)
        response = self.chat_service.ListAccounts(request, None)

        self.assertEqual(response.status, "success")
        self.assertIn("alice", response.usernames)

    def test_announce_leader(self):
        request = chat_pb2.CoordinatorMessage(new_leader_address="127.0.0.1:50051")
        response = self.chat_service.AnnounceLeader(request, None)
        self.assertEqual(response.status, "success")
        self.assertEqual(self.chat_service.leader_address, "127.0.0.1:50051")
        self.assertFalse(self.chat_service.is_leader)

    @patch("server.chat_pb2_grpc.ChatServiceStub")
    def test_announce_new_leader(self, mock_stub_class):
        self.chat_service.replica_addresses = ["127.0.0.1:50055"]
        stub = MagicMock()
        mock_stub_class.return_value = stub

        self.chat_service.AnnounceNewLeader()

        self.assertTrue(self.chat_service.is_leader)
        stub.AnnounceLeader.assert_called_once()


    def test_listen_for_messages_yields_message(self):
        q = queue.Queue()
        msg = chat_pb2.Message(id=1, sender="bob", message="hi")
        q.put(msg)
        self.chat_service.online_users["alice"] = q

        request = chat_pb2.ListenForMessagesRequest(username="alice")
        context = MagicMock()

        generator = self.chat_service.ListenForMessages(request, context)
        self.assertEqual(next(generator), msg)

    def test_get_replica_addresses(self):
        self.chat_service.replica_addresses = ["127.0.0.1:50053", "127.0.0.1:50054"]
        response = self.chat_service.GetReplicaAddresses(None, None)
        self.assertIn("127.0.0.1:50053", response.replica_addresses)

    def test_follower_sync_updates_storage(self):
        self.chat_service.is_leader = False
        self.chat_service.leader_address = "127.0.0.1:50051"  # 🧠 Fix: needed for .split(":")
        self.chat_service.leader_stub = MagicMock()
        self.chat_service.leader_stub.SyncData.return_value = chat_pb2.SyncDataResponse(
            status="success",
            messages=[
                chat_pb2.MessageData(id=1, sender="alice", recipient="bob", message="hi", status="read")
            ],
            users=[
                chat_pb2.UserData(username="alice", password_hash=b"hash")
            ],
            replica_addresses=[],
            online_usernames=["alice"]
        )

        response = self.chat_service.FollowerSync(chat_pb2.FollowerSyncDataRequest(leader_address="127.0.0.1:50051"), None)
        self.assertEqual(response.status, "success")
        self.assertIn("alice", self.chat_service.online_users)

    def test_send_message_stored_when_recipient_offline(self):
        self.mock_storage.send_message.return_value = {"status": "success"}
        self.chat_service.online_users = {}

        request = chat_pb2.SendMessageRequest(username="alice", recipient="bob", message="hi")
        response = self.chat_service.SendMessage(request, None)

        self.assertEqual(response.status, "success")
        self.assertIn("stored", response.message)

    @patch("server.grpc")
    def test_broadcast_sync_handles_errors(self, mock_grpc):
        replica = MagicMock()
        replica.FollowerSync.side_effect = mock_grpc.RpcError("sync error")
        self.chat_service.replicas = [replica]

        self.chat_service.Broadcast_Sync()


    @patch.object(ChatService, "AnnounceNewLeader")
    def test_initiate_election_becomes_leader(self, mock_announce):
        self.chat_service.replica_addresses = ["127.0.0.1:50050"]  # lower than self.port
        self.chat_service.port = 50052
        self.chat_service.initiate_election()
        mock_announce.assert_called_once()

    def test_start_election_no_response(self):
        self.chat_service.replica_addresses = ['127.0.0.1:50053']
        with patch('chat_pb2_grpc.ChatServiceStub') as mock_stub_class:
            stub = MagicMock()
            stub.StartElection.side_effect = grpc.RpcError("No response")
            mock_stub_class.return_value = stub

            with patch.object(self.chat_service, 'AnnounceNewLeader') as mock_announce:
                self.chat_service.initiate_election()
                mock_announce.assert_called_once()

    def test_read_messages_replica_failure(self):
        self.chat_service.is_leader = True
        
        mock_replica1 = MagicMock()
        mock_replica1.ReadMessages.side_effect = grpc.RpcError("Replica 1 failed")
        
        mock_replica2 = MagicMock()
        mock_replica2.ReadMessages.side_effect = grpc.RpcError("Replica 2 failed")
        
        self.chat_service.replicas = [mock_replica1, mock_replica2]
        
        self.mock_storage.read_messages.return_value = {
            "status": "error",
            "messages": []
        }
        
        request = chat_pb2.ReadMessagesRequest(username="alice", limit=1)
        response = self.chat_service.ReadMessages(request, None)
        
        self.assertEqual(response.status, "error")
        self.assertEqual(len(response.messages), 0)

    def test_list_accounts_replica_failure(self):
        self.chat_service.is_leader = True
        
        mock_replica1 = MagicMock()
        mock_replica1.ListAccounts.side_effect = grpc.RpcError("Replica 1 failed")
        
        mock_replica2 = MagicMock()
        mock_replica2.ListAccounts.side_effect = grpc.RpcError("Replica 2 failed")
        
        self.chat_service.replicas = [mock_replica1, mock_replica2]
        
        self.mock_storage.list_accounts.return_value = {
            "usernames": ["alice", "bob"]
        }
        
        request = chat_pb2.ListAccountsRequest(page_num=1)
        response = self.chat_service.ListAccounts(request, None)
        
        self.assertEqual(response.status, "error")
        self.assertEqual(len(response.usernames), 0)

if __name__ == "__main__":
    unittest.main()
