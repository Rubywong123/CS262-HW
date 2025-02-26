
# CS262 - RPC Communication
Codebase for CS262 Assignment - Communication 2: RPC

This is a Python-based chat client that allows users to communicate with a server using gRPC. The application supports functionalities such as user registration/login, online messaging, offline messaging, and account management through a graphical user interface (GUI) built with Tkinter

## Features
- **User Authentication:** If a user has already signed up, they will be prompted to input a password to sign in. If the username is not recognized by the database, the user will be prompted to register with a username and password.
- **Messaging System:** Send and receive messages in real time. Users can send messages to offline users, and those users can retrieve messages when they come online.
- **Account Management:** List accounts, delete messages, and delete user accounts.
- **GUI Interface:** Built with Tkinter, providing an intuitive and user-friendly chat experience.

## gRPC
The communication between the client and server is implemented using gRPC (Google Remote Procedure Call). Some benefits of using gRPC are efficient binary serialization, built-in streaming support, and automatic code generation from the `chat.proto` file, which defines the remote procedures and message structures. 

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/Rubywong123/CS262-HW
   ```
2. Navigate to the HW2 folder
   ```sh
   cd CS262-HW/HW2
   ```
3. Set up the gRPC service stubs:
   ```sh
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto
   ```
4. Run the server:
   ```sh
   python server.py
   ```
5. Run the client:

   - If connecting to a server on the same machine:

     ```sh
     python gui.py
     ```

   - If connecting to a **remote server**, specify the server’s IP:

     ```sh
     python gui.py --host <server_ip>
     ```

## Usage
1. Start the client and enter login credentials. If the account does not exist, it will be created automatically.  
2. Use the provided buttons to interact with the chat system:  
   - **List Accounts**: View all registered users.  
   - **Send Message**: Enter a recipient's username and type a message to send.  
   - **Read Messages**: Retrieve and display the messages received. Users can specify the number of messages they want to retrieve.   
   - **Delete Message**: Delete the most recent message sent to a specific user.  
   - **Delete Account**: Permanently delete your account after confirming your password.   
3. Messages are displayed in the chat window with real-time updates.
4. To exit, simply close the client window.  


## Test Coverage
To run the tests and generate a coverage report, use the following command:

```bash
pytest --cov=. tests/
```

The test coverage statistics for the codebase are as follows:

| File              | Statements | Missing | Coverage |
|------------------|------------|----------|------------|
| client.py        | 81         | 18       | 78%        |
| gui.py           | 160        | 27       | 83%        |
| server.py        | 79         | 20       | 75%        |
| storage.py       | 79         | 3        | 96%        |
| **TOTAL**        | **390**    | **68**   | **83%**    |
