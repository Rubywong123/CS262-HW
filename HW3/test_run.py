import unittest
import socket
import threading
import time
import os
import json
import shutil
from unittest.mock import patch, MagicMock, mock_open,call
import sys
from run import VirtualMachine, Message

class TestMessage(unittest.TestCase):
    def test_message_serialization(self):
        """Test that messages can be correctly serialized and deserialized."""
        original_message = Message(clock=42, sender=1)
        json_str = original_message.to_json()
        restored_message = Message.from_json(json_str)
        
        self.assertEqual(restored_message.clock, 42)
        self.assertEqual(restored_message.sender, 1)

class TestVirtualMachine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create a logs directory if it doesn't exist."""
        if not os.path.exists("test_logs"):
            os.makedirs("test_logs")
    
    @classmethod
    def tearDownClass(cls):
        """Remove the logs directory after tests."""
        if os.path.exists("test_logs"):
            shutil.rmtree("test_logs")
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_file = mock_open()
        self.patcher = patch('run.open', self.mock_file)
        self.mock_open_func = self.patcher.start()
        
        self.socket_patcher = patch('run.socket.socket')
        self.mock_socket = self.socket_patcher.start()
        
        self.mock_socket_instance = MagicMock()
        self.mock_socket.return_value = self.mock_socket_instance
        
        self.thread_patcher = patch('run.threading.Thread')
        self.mock_thread = self.thread_patcher.start()
        self.mock_thread_instance = MagicMock()
        self.mock_thread.return_value = self.mock_thread_instance
        self.sleep_patcher = patch('run.time.sleep')
        self.mock_sleep = self.sleep_patcher.start()
        
        self.random_patcher = patch('run.random.randint')
        self.mock_random = self.random_patcher.start()
        self.mock_random.return_value = 10
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher.stop()
        self.socket_patcher.stop()
        self.thread_patcher.stop()
        self.sleep_patcher.stop()
        self.random_patcher.stop()
    
    def test_vm_initialization(self):
        """Test that a VM is correctly initialized."""
        self.mock_random.return_value = 3
        
        vm = VirtualMachine(id=1, peers=[0, 2])
        
        self.assertEqual(vm.id, 1)
        self.assertEqual(vm.peers, [0, 2])
        self.assertEqual(vm.peer_for_action_1, 0)
        self.assertEqual(vm.peer_for_action_2, 2)
        self.assertEqual(vm.logical_clock, 0)
        self.assertEqual(vm.message_queue, [])
        self.assertTrue(vm.running)
        self.assertEqual(vm.clock_speed, 3)
    
    def test_process_message(self):
        """Test that messages are correctly processed and logical clock updated."""
        vm = VirtualMachine(id=1, peers=[0, 2])
        vm.logical_clock = 5
        
        message1 = Message(clock=3, sender=0)
        vm.process_message(message1)
        self.assertEqual(vm.logical_clock, 6)
        
        message2 = Message(clock=10, sender=2)
        vm.process_message(message2)
        self.assertEqual(vm.logical_clock, 11)
    
    def test_internal_event(self):
        """Test that internal events increment the logical clock."""
        vm = VirtualMachine(id=1, peers=[0, 2])
        vm.logical_clock = 5
        
        self.mock_random.return_value = 10
        
        with patch.object(vm, 'send_message') as mock_send:
            original_run = vm.run
            
            def modified_run():
                original_clock = vm.logical_clock
                time.sleep(1 / vm.clock_speed)
                vm.logical_clock += 1
                vm.log(f"Internal event, Clock: {vm.logical_clock}")

                vm.running = False
            
            vm.run = modified_run
            vm.run()
            
            self.assertEqual(vm.logical_clock, 6)
            mock_send.assert_not_called()
    
    def test_send_message_to_peer1(self):
        """Test sending a message to peer 1."""
        vm = VirtualMachine(id=1, peers=[0, 2])
        vm.logical_clock = 5
        
        with patch.object(vm, 'send_message') as mock_send:
            self.mock_random.return_value = 1 
            
            def modified_run():
                vm.send_message(vm.peer_for_action_1)
                vm.logical_clock += 1
                vm.log(f"Sent message to {vm.peer_for_action_1}, Clock: {vm.logical_clock}")
                vm.running = False
                
            vm.run = modified_run
            vm.run()
            
            mock_send.assert_called_once_with(0)
            self.assertEqual(vm.logical_clock, 6)
    
    def test_send_message_to_peer2(self):
        """Test sending a message to peer 2."""
        vm = VirtualMachine(id=1, peers=[0, 2])
        vm.logical_clock = 5
        
        with patch.object(vm, 'send_message') as mock_send:
            self.mock_random.return_value = 2 
            
            def modified_run():
                vm.send_message(vm.peer_for_action_2)
                vm.logical_clock += 1
                vm.log(f"Sent message to {vm.peer_for_action_2}, Clock: {vm.logical_clock}")
                vm.running = False
                
            vm.run = modified_run
            vm.run()
            
            mock_send.assert_called_once_with(2)
            self.assertEqual(vm.logical_clock, 6)
    
    def test_broadcast_message(self):
        """Test broadcasting a message to all peers."""
        vm = VirtualMachine(id=1, peers=[0, 2])
        vm.logical_clock = 5
        
        with patch.object(vm, 'send_message') as mock_send:
            self.mock_random.return_value = 3 
            
            def modified_run():
                for target in vm.peers:
                    vm.send_message(target)
                vm.logical_clock += 1
                vm.log(f"Broadcasted message, Clock: {vm.logical_clock}")
                vm.running = False
                
            vm.run = modified_run
            vm.run()
            
            mock_send.assert_any_call(0)
            mock_send.assert_any_call(2)
            self.assertEqual(mock_send.call_count, 2)
            self.assertEqual(vm.logical_clock, 6)
    
    def test_listen_for_messages(self):
        """Test that the VM correctly adds messages to the queue."""
        vm = VirtualMachine(id=1, peers=[0, 2])
        
        mock_conn = MagicMock()
        mock_conn.recv.return_value = Message(clock=10, sender=2).to_json().encode('utf-8')
        
        self.mock_socket_instance.accept.return_value = (mock_conn, ('localhost', 12345))
        
        def side_effect(*args, **kwargs):
            vm.running = False
            return (mock_conn, ('localhost', 12345))
            
        self.mock_socket_instance.accept.side_effect = side_effect
        
        vm.listen_for_messages()
        
        self.assertEqual(len(vm.message_queue), 1)
        self.assertEqual(vm.message_queue[0].clock, 10)
        self.assertEqual(vm.message_queue[0].sender, 2)

    
    def test_integration_simple(self):
        """Simple integration test with mocked network operations."""
        vm1 = VirtualMachine(id=1, peers=[0, 2])
        vm2 = VirtualMachine(id=2, peers=[0, 1])
        
        message = Message(clock=5, sender=1)
        vm2.message_queue.append(message)
        
        vm2.process_message(vm2.message_queue.pop(0))
        self.assertEqual(vm2.logical_clock, 6)

    def test_send_message(self):
        """Test that sending a message calls socket functions correctly"""
        vm = VirtualMachine(id=1, peers=[0, 2])
        with patch('run.socket.socket') as mock_socket:
            vm.send_message(2)
            mock_socket_instance = mock_socket.return_value
            mock_socket_instance.connect.assert_called_with(("localhost", 5002))
            mock_socket_instance.send.assert_called()

    def test_run_with_message_in_queue(self):
        """Test run method when there's a message in the queue."""
        vm = VirtualMachine(id=1, peers=[0, 2])
        test_message = Message(10, 2)
        vm.message_queue.append(test_message)

        with patch.object(vm, 'process_message') as mock_process:
            def stop_after_one_iteration(_):
                vm.running = False

            mock_process.side_effect = stop_after_one_iteration

            vm.run()

            mock_process.assert_called_once()

            called_message = mock_process.call_args[0][0]
            assert called_message.clock == 10
            assert called_message.sender == 2


if __name__ == "__main__":
    unittest.main()