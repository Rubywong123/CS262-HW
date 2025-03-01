import socket
import threading
import time
import random
import json
import os

class Message:
    def __init__(self, clock, sender):
        self.clock = clock
        self.sender = sender
    
    def to_json(self):
        return json.dumps({"clock": self.clock, "sender": self.sender})
    
    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Message(data["clock"], data["sender"])

class VirtualMachine:
    def __init__(self, id, peers):
        self.id = id
        self.clock_speed = random.randint(1, 6)
        self.logical_clock = 0
        self.message_queue = []
        self.peers = peers
        self.peer_for_action_1 = peers[0]
        self.peer_for_action_2 = peers[1]
        self.log_file = open(f'logs/machine_{id}.log', 'w')
        self.running = True
        
        # Start listening for messages
        self.listener_thread = threading.Thread(target=self.listen_for_messages)
        self.listener_thread.start()
        
    def listen_for_messages(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("localhost", 5000 + self.id))
        server.listen(5)
        # check running status periodically
        server.settimeout(1)
        while self.running:
            try:
                conn, addr = server.accept()
                data = conn.recv(1024).decode('utf-8')
                if data:
                    self.message_queue.append(Message.from_json(data))
                conn.close()
            except socket.timeout:
                # Timeout to check the running status
                continue
        server.close()


    def send_message(self, target_id):
        message = Message(self.logical_clock, self.id)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 5000 + target_id))
        client.send(message.to_json().encode('utf-8'))
        client.close()

    def process_message(self, message):
        self.logical_clock = max(self.logical_clock, message.clock) + 1
        self.log(f"Received message from {message.sender}, Clock: {self.logical_clock}")

    def log(self, entry):
        timestamp = time.time()
        log_entry = f"{timestamp} - Machine {self.id}: {entry}\n"
        if not self.log_file.closed:
            self.log_file.write(log_entry)
        print(log_entry.strip())

    def run(self):
        while self.running:
            time.sleep(1 / self.clock_speed)
            # check for new messages
            if self.message_queue:
                message = self.message_queue.pop(0)
                self.process_message(message)
            else:
                # Perform internal event or send message
                action = random.randint(1, 10)
                if action == 1 and self.peer_for_action_1 is not None:
                    self.send_message(self.peer_for_action_1)
                    self.logical_clock += 1
                    self.log(f"Sent message to {self.peer_for_action_1}, Clock: {self.logical_clock}")
                elif action == 2 and self.peer_for_action_2 is not None:
                    self.send_message(self.peer_for_action_2)
                    self.logical_clock += 1
                    self.log(f"Sent message to {self.peer_for_action_2}, Clock: {self.logical_clock}")
                elif action == 3:
                    for target in self.peers:
                        self.send_message(target)
                    self.logical_clock += 1
                    self.log(f"Broadcasted message, Clock: {self.logical_clock}")
                else:
                    self.logical_clock += 1
                    self.log(f"Internal event, Clock: {self.logical_clock}")

if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")
    machines = [VirtualMachine(i, [j for j in range(3) if j != i]) for i in range(3)]
    threads = [threading.Thread(target=machine.run) for machine in machines]
    for thread in threads:
        thread.start()
    
    time.sleep(60)
    
    for machine in machines:
        # stop the machine and close the log file
        # avoid improper closing
        machine.running = False
        machine.log_file.close()
    
    # wait for threads to finish
    for thread in threads:
        thread.join()