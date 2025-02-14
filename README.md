# CS262 - Design Exercise - Wire Protocol
Codebase for CS262 Design Exercise 1 - Wire Protocol

This is a Python-based chat client that allows users to communicate with a server using either a JSON protocol or a custom protocol. The application supports functionalities such as user registration/login, online messaging, offline messaging, and account management through a graphical user interface (GUI) built with Tkinter

## Features
- **User Authentication:** If a user has already signed up, they will be prompted to input a password to sign in. If the username is not recognized by the database, the user will be prompted to register with a username and password.
- **Messaging System:** Send and receive messages in real time. Users can send messages to offline users, and those users can retrieve messages when they come online.
- **Account Management:** List accounts, delete messages, and delete user accounts.
- **GUI Interface:** Built with Tkinter, providing an intuitive and user-friendly chat experience.

## JSON Protocol
The JSONProtocol provides a simple, text-based communication protocol using JSON serialization. It allows structured data to be sent over a socket connection in an easy-to-read and platform-independent format. Each message consists of:

1. A 4-byte big-endian length prefix indicating the size of the JSON-encoded message.

2. The actual JSON message encoded as UTF-8.

## Custom Protocol 
The CustomProtocol is a binary communication protocol designed for structured and efficient message exchange. It encodes data in a compact, length-prefixed format for various message types, reducing overhead compared to text-based protocols. Messages consist of:

- A 4-byte message length prefix.

- A 1-byte action type identifier.

- A 1-byte field count.

- Variable-length fields encoded using the length-prefixed format.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/Rubywong123/CS262-HW
   ```
2. Run the server:
   ```sh
   python server.py
   ```
3. **Run the client**:

   - If connecting to a server on the same machine:

     ```sh
     python client.py
     ```

   - If connecting to a **remote server**, specify the server’s IP:

     ```sh
     python client.py --host <server_ip>
     ```

## Usage
1. Start the client and enter login credentials. If the account does not exist, it will be created automatically.  
2. Use the provided buttons to interact with the chat system:  
   - **List Accounts**: View all registered users.  
   - **Send Message**: Enter a recipient's username and type a message to send.  
   - **Read Messages**: Retrieve and display the messages received. Users can specify the number of messages they want to retrieve.   
   - **Delete Message**: Remove a specific message by entering its message ID.  
   - **Delete Account**: Permanently delete your account after confirming your password.   
3. Messages are displayed in the chat window with real-time updates.
4. To exit, simply close the client window.  

## Known Issues
- The GUI might freeze if the server connection is lost unexpectedly.
- Ensure the server is running before starting the client.

## Test Coverage
To run the tests and generate a coverage report, use the following command:

```bash
pytest --cov=. tests/
```

The test coverage statistics for the codebase are as follows:

| File              | Statements | Missing | Coverage |
|------------------|------------|----------|------------|
| client.py        | 168        | 24       | 86%        |
| db_viewer.py     | 16         | 1        | 94%        |
| protocol.py      | 124        | 16       | 87%        |
| server.py        | 86         | 17       | 80%        |
| storage.py       | 59         | 1        | 98%        |
| test_client.py   | 110        | 1        | 99%        |
| test_db_viewer.py| 25         | 1        | 96%        |
| test_protocol.py | 115        | 1        | 99%        |
| test_server.py   | 73         | 1        | 99%        |
| test_storage.py  | 64         | 1        | 98%        |
| **TOTAL**        | **849**    | **64**   | **92%**    |