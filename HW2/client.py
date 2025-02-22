import grpc
import chat_pb2
import chat_pb2_grpc

def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    print("Welcome to the Chat App!")
    
    username = input("Enter username: ")
    password = input("Enter password: ")

    login_response = stub.Login(chat_pb2.LoginRequest(username=username, password=password))
    if login_response.status != "success":
        print("Login failed:", login_response.message)
        return

    print("Login successful!")
    
    while True:
        print("\nOptions:")
        print("1. List accounts")
        print("2. Send message")
        print("3. Read messages")
        print("4. Delete message")
        print("5. Delete account")
        print("6. Exit")

        choice = input("Enter choice: ")
        
        if choice == "1":
            response = stub.ListAccounts(chat_pb2.ListAccountsRequest(page_num=1))
            print("Accounts:", response.usernames)

        elif choice == "2":
            recipient = input("Recipient username: ")
            message = input("Message: ")
            response = stub.SendMessage(chat_pb2.SendMessageRequest(recipient=recipient, message=message))
            print(response.status, response.message)

        elif choice == "3":
            response = stub.ReadMessages(chat_pb2.ReadMessagesRequest(username=username, limit=10))
            for msg in response.messages:
                print(f"From {msg.sender}: {msg.message}")

        elif choice == "4":
            message_id = int(input("Enter message ID to delete: "))
            response = stub.DeleteMessage(chat_pb2.DeleteMessageRequest(message_id=message_id))
            print(response.status, response.message)

        elif choice == "5":
            confirm = input("Are you sure you want to delete your account? (yes/no): ")
            if confirm.lower() == "yes":
                response = stub.DeleteAccount(chat_pb2.DeleteAccountRequest(username=username, password=password))
                print(response.status, response.message)
                if response.status == "success":
                    break

        elif choice == "6":
            break

if __name__ == "__main__":
    run()
