import struct
import json

class JSONProtocol:
    @staticmethod
    def send(socket, data):
        message = json.dumps(data).encode('utf-8')
        socket.sendall(struct.pack("I", len(message)) + message)

    @staticmethod
    def receive(socket):
        data_length = struct.unpack("I", socket.recv(4))[0]
        return json.loads(socket.recv(data_length).decode('utf-8'))

class CustomProtocol:
    @staticmethod
    def send(socket, data):
        message = f"{data['action']}|{data.get('username', '')}|{data.get('password', '')}|{data.get('message', '')}".encode('utf-8')
        socket.sendall(struct.pack("I", len(message)) + message)

    @staticmethod
    def receive(socket):
        data_length = struct.unpack("I", socket.recv(4))[0]
        data = socket.recv(data_length).decode('utf-8').split("|")
        return {"action": data[0], "username": data[1], "password": data[2], "message": data[3]}
