import sys
import chatroom_client
import grpc
import chatroom_pb2_grpc
from chatroom_server import ChatRoom
from concurrent import futures

# Start the server
port = '5555'
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
chatroom_pb2_grpc.add_ChatRoomServicer_to_server(ChatRoom(), server)
server.add_insecure_port('[::]:' + port)
server.start()
print("Server started on port " + port)

# Start the client
with grpc.insecure_channel(f'localhost:{port}') as channel:
    stub = chatroom_pb2_grpc.ChatRoomStub(channel)
    logged_in = None


    
    # Test user creation and when username already exists
    assert chatroom_client.CreateUser(stub, "user1", "pass1", test=True) == (True, "User user1 created successfully")
    assert chatroom_client.CreateUser(stub, "user1", "pass1", test=True) == (False, "Username already exists")

    # Test login and when user already logged in
    assert chatroom_client.Login(stub, status=None, username="user1", password="pass1", test=True) == (True, "User user1 login successful", "user1")
    assert chatroom_client.Login(stub, status=None, username="user1", password="pass1", test=True) == (False, "User user1 is already online")

    # Test logout and when user is not logged in
    assert chatroom_client.Logout(stub, status="user1", test=True) == (True, "User user1 logged out successfully", None)
    assert chatroom_client.Logout(stub, status="user1", test=True) == (False, "User user1 is already offline")

    # Test login when password is wrong and user does not exist
    assert chatroom_client.Login(stub, status=None, username="user1", password="pass2", test=True) == (False, "Incorrect password for user user1")
    assert chatroom_client.Login(stub, status=None, username="user2", password="pass1", test=True) == (False, "User user2 does not exist")

   



print("All tests passed!")

server.wait_for_termination()