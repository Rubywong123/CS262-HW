import json
import struct 

class JSONProtocol:
    @staticmethod
    def send(socket, data):
        message = json.dumps(data).encode('utf-8')
        message_length = len(message).to_bytes(4, byteorder='big')
        total_size = len(message) + 4
        print(f"[JSONProtocol] Sending {total_size} bytes: {message}")
        socket.sendall(message_length + message)

    @staticmethod
    def receive(socket):
        data_length_bytes = socket.recv(4)
        if not data_length_bytes:
            return None
        data_length = int.from_bytes(data_length_bytes, byteorder='big')
        data = socket.recv(data_length).decode('utf-8')
        print(f"[JSONProtocol] Received {data_length + 4} bytes: {data}")
        return json.loads(data)


class CustomProtocol:
    @staticmethod
    def encode_length_prefixed_field(value):
        """
        The CustomProtocol provides a binary-encoded wire protocol for communication. 
        It encodes a string field with a length prefix.
        - If the length is < 255, encode as a single-byte length
        - If the length is >= 255, prefix with `0x00` and use a 4-byte big-endian length.
        """
        value_bytes = value.encode("utf-8")
        length = len(value_bytes)

        # if length < 255, use single-byte length
        if length < 255:
            return struct.pack(">B", length) + value_bytes
        # if length >= 255 we use 0-byte followed by 4-byte length
        else:
            return struct.pack(">BI", 0, length) + value_bytes

    @staticmethod
    def decode_length_prefixed_field(socket):
        """
        Read a length-prefixed field from the socket.
        - If the first byte is nonzero, it represents the length.
        - If the first byte is 0x00, read the next 4 bytes for the length.
        """
        length_prefix = socket.recv(1)
        if not length_prefix:
            return None
        
        # read 1-byte length
        length = struct.unpack(">B", length_prefix)[0]
        # read 4-byte length if prefix is 0
        if length == 0:
            length = struct.unpack(">I", socket.recv(4))[0]

        return socket.recv(length).decode("utf-8")

    @staticmethod
    def send(socket, action_type, **kwargs):
        """
        Send a binary-encoded message over the socket.
        Each messages consists of:
        - 1 byte: Action type (e.g. 1=login)
        - 1 byte: Field count
        - Variable-length fields (each with a length prefix)
        """
        fields = []

        # login 
        if action_type == 1:
            fields.append(CustomProtocol.encode_length_prefixed_field(kwargs["username"]))
            fields.append(CustomProtocol.encode_length_prefixed_field(kwargs["password"]))
        # list account
        elif action_type == 2:
            fields.append(struct.pack(">B", kwargs["page_num"]))
        # send message
        elif action_type == 3: 
            fields.append(CustomProtocol.encode_length_prefixed_field(kwargs["recipient"]))
            fields.append(CustomProtocol.encode_length_prefixed_field(kwargs["message"]))
        # read message
        elif action_type == 4:
            fields.append(struct.pack(">B", kwargs["limit"]))
        # delete message
        elif action_type == 5:
            fields.append(CustomProtocol.encode_length_prefixed_field(kwargs["recipient"]))
            fields.append(struct.pack(">I", kwargs["message_id"]))
        # delete account 
        elif action_type == 6:
            fields.append(CustomProtocol.encode_length_prefixed_field(kwargs["password"]))
        elif action_type == 7:
            for key, value in kwargs.items():
                fields.append(CustomProtocol.encode_length_prefixed_field(str(value)))

        field_count = len(fields)
        print(f"[DEBUG] kwargs: {kwargs.items()}")
        print(f"[DEBUG] Fields: {fields}")
        message = struct.pack(">BB", action_type, field_count) + b"".join(fields)
        message_length = struct.pack(">I", len(message))  # 4-byte message length prefix

        print(f"[CustomProtocol] Sending {len(message) + 4} bytes")
        socket.sendall(message_length + message)

    @staticmethod
    def receive(socket):
        """
        Receive and decode a binary message.
        Each received message consit of:
        - 4-byte for overall message length
        - 1-byte action type
        - 1-byte field count
        - variable-length fields (including 1-byte individual field message length)
        """
        data_length_bytes = socket.recv(4)
        if not data_length_bytes:
            return None

        data_length = struct.unpack(">I", data_length_bytes)[0]
        data = socket.recv(data_length)
        print(f"[DEBUG] Raw Data Received: {data.hex()}")

        if not data:
            return None
        # Read action type and field count
        action_type, field_count = struct.unpack(">BB", data[:2])
        offset = 2

        action_map = {
            1: "login",
            2: "list_accounts",
            3: "send_message",
            4: "read_messages",
            5: "delete_message",
            6: "delete_account",
            7: "response"
        }

        action = action_map.get(action_type, "unknown")
        data_dict = {"action": action}

        for i in range(field_count):
            if action == "login":
                print(field_count)
                key = "username" if i == 0 else "password"
                field_value, field_size = CustomProtocol._extract_field(data, offset)
                data_dict[key] = field_value
                offset += field_size

            elif action == "list_accounts":
                data_dict['page_num'] = struct.unpack(">B", data[offset:offset + 1])[0]
                offset += 1

            elif action == "send_message":
                key = "recipient" if i == 0 else "message"
                field_value, field_size = CustomProtocol._extract_field(data, offset)
                data_dict[key] = field_value
                offset += field_size

            elif action == "read_messages":
                data_dict["limit"] = struct.unpack(">B", data[offset:offset + 1])[0]
                offset += 1 

            elif action == "delete_message":
                if i == 0:
                    field_value, field_size = CustomProtocol._extract_field(data, offset)
                    data_dict["recipient"] = field_value
                    offset += field_size
                else:
                    data_dict["message_id"] = struct.unpack(">I", data[offset:offset + 4])[0]
                    offset += 4

            elif action == "delete_account":
                key = "password"
                field_value, field_size = CustomProtocol._extract_field(data, offset)
                data_dict[key] = field_value
                offset += field_size

            elif action == "response":
                key = 'status' if i == 0 else 'message'
                value, field_size = CustomProtocol._extract_field(data, offset)
                offset += field_size
                data_dict[key] = value
            
        print(f"[CustomProtocol] Received {data_length + 4} bytes: {data_dict}")
        return data_dict
    
    @staticmethod
    def _extract_field(data, offset, encrypted=False):
        """
        Extract a length-prefixed field from binary data.
        Returns the extracted value and the number of bytes read.
        """
        # Read 1-byte length
        length = struct.unpack(">B", data[offset:offset + 1])[0]
        if length == 0:
            # Read 4-byte length if prefix is 0
            length = struct.unpack(">I", data[offset + 1:offset + 5])[0] 
            # Move past the 4-byte length field
            offset += 4

        value = data[offset + 1:offset + 1 + length].decode("utf-8") if not encrypted else data[offset + 1:offset + 1 + length]
        return value, (1 + length if length < 255 else 5 + length)


