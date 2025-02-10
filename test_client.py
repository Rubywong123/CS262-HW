import socket
import struct

# Connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 65432))

def send_message(action_type, **kwargs):
    """
    Helper function to send a message using the custom binary protocol.
    """
    fields = []
    
    # Encode fields dynamically
    if action_type == 1:  # Login (username, password)
        fields.append(kwargs["username"].encode("utf-8"))
        fields.append(kwargs["password"].encode("utf-8"))
    elif action_type == 3:  # Send message (sender, recipient, message)
        fields.append(kwargs["sender"].encode("utf-8"))
        fields.append(kwargs["recipient"].encode("utf-8"))
        fields.append(kwargs["message"].encode("utf-8"))
    elif action_type == 4:  # Read messages (limit)
        fields.append(struct.pack(">B", kwargs["limit"]))  # 1-byte integer
    elif action_type == 5:  # Delete message (recipient, message_id)
        fields.append(kwargs["recipient"].encode("utf-8"))
        fields.append(struct.pack(">I", kwargs["message_id"]))  # 4-byte integer
    elif action_type == 6:  # Delete account (no fields)
        pass

    field_count = len(fields)
    packed_message = struct.pack(">BB", action_type, field_count) + b"".join(fields)
    message_length = struct.pack(">I", len(packed_message))  # 4-byte length prefix

    client.sendall(message_length + packed_message)
    print(f"[DEBUG] Sent {len(packed_message) + 4} bytes")

def receive_response():
    """
    Receives a response from the server.
    """
    data_length_bytes = client.recv(4)
    if not data_length_bytes:
        print("[ERROR] No response received")
        return None
    data_length = struct.unpack(">I", data_length_bytes)[0]
    data = client.recv(data_length)

    print(f"[DEBUG] Received {data_length + 4} bytes: {data}")

# Test cases
print("Logging in...")
send_message(1, username="alice", password="securepass")
receive_response()

print("Sending message...")
send_message(3, sender="alice", recipient="bob", message="Hello, Bob!")
receive_response()

print("Reading messages...")
send_message(4, limit=5)
receive_response()

print("Deleting message...")
send_message(5, recipient="bob", message_id=123)
receive_response()

print("Deleting account...")
send_message(6)
receive_response()

# Close connection
client.close()
