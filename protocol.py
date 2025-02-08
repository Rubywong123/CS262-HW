import json

class JSONProtocol:
    @staticmethod
    def send(socket, data):
        message = json.dumps(data).encode('utf-8')
        message_length = len(message).to_bytes(4, byteorder='big')  # Encode length in 4 bytes
        socket.sendall(message_length + message)

    @staticmethod
    def receive(socket):
        data_length_bytes = socket.recv(4)
        if not data_length_bytes:
            return None
        data_length = int.from_bytes(data_length_bytes, byteorder='big')
        data = socket.recv(data_length).decode('utf-8')
        return json.loads(data)


class CustomProtocol:
    """
    Custom wire protocol with a pipe (`|`) separator.
    Format: action|data (where data is a flexible key-value structure)
    """

    @staticmethod
    def send(socket, data):
        """
        Convert data into a compact string format.
        """
        action = data.get("action", "")

        serialized_data = "&".join(f"{k}={v}" for k, v in data.items() if k != "action")

        message_str = f"{action}|{serialized_data}".encode('utf-8')

        message_length = len(message_str).to_bytes(4, byteorder='big')
        socket.sendall(message_length + message_str)

    @staticmethod
    def receive(socket):
        """
        Read and decode a message.
        """
        data_length_bytes = socket.recv(4)
        if not data_length_bytes:
            return None
        data_length = int.from_bytes(data_length_bytes, byteorder='big')
        data = socket.recv(data_length).decode('utf-8')

        parts = data.split("|", 1)
        action = parts[0]
        data_dict = {}

        if len(parts) > 1 and parts[1]:
            for item in parts[1].split("&"):
                key_value = item.split("=", 1)
                if len(key_value) == 2:
                    key, value = key_value
                    if key in ("message_id", "limit"):
                        data_dict[key] = int(value) if value.isdigit() else value
                    else:
                        data_dict[key] = value

        data_dict["action"] = action
        return data_dict

