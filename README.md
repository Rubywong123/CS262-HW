# CS262 - Design Exercise - Wire Protocol
Codebase for CS262 Design Exercise 1 - Wire Protocol

This is a Python-based chat client that allows users to communicate with a server using either a JSON protocol or a custom protocol. The application supports functionalities such as user registration/login, online messaging, offline messaging, and account management through a graphical user interface (GUI) built with Tkinter.

## Features
- **User Authentication:** If a user has already signed up, they will be prompted to input a password to sign in. If the username is not recognized by the database, the user will be prompted to register with a username and password.
- **Messaging System:** Send and receive messages in real time. Users can send messages to offline users, and those users can retrieve messages when they come online.
- **Account Management:** List accounts, delete messages, and delete user accounts.
- **GUI Interface:** Built with Tkinter, providing an intuitive and user-friendly chat experience.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/Rubywong123/CS262-HW
   ```
2. Run the server:
   ```sh
   python server.py
   ```
3. Run the client:
   ```sh
   python client.py
   ```

## Usage
1. Start the client and enter login credentials.
2. Use the provided buttons to send messages, read messages, list accounts, or manage the account.
3. Messages are displayed in the chat window with real-time updates.

## Known Issues
- The GUI might freeze if the server connection is lost unexpectedly.
- Ensure the server is running before starting the client.

## Test Coverage
The test coverage statistics for the codebase are as follows:

| File              | Statements | Missing | Coverage |
|------------------|------------|----------|------------|
| client.py        | 154        | 32       | 79%        |
| db_viewer.py     | 16         | 1        | 94%        |
| protocol.py      | 124        | 16       | 87%        |
| server.py        | 86         | 17       | 80%        |
| storage.py       | 59         | 1        | 98%        |
| test_client.py   | 110        | 1        | 99%        |
| test_db_viewer.py| 25         | 1        | 96%        |
| test_protocol.py | 115        | 1        | 99%        |
| test_server.py   | 73         | 1        | 99%        |
| test_storage.py  | 64         | 1        | 98%        |
| **TOTAL**        | **826**    | **72**   | **91%**    |

