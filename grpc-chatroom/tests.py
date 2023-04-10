import sys
import chatroom_client
import grpc
import chatroom_pb2
import chatroom_pb2_grpc
from chatroom_server import ChatRoom
from concurrent import futures
import time

# Start the server
port = '5555' # Default port for testing, can be changed
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
chatroom_pb2_grpc.add_ChatRoomServicer_to_server(ChatRoom(), server)
server.add_insecure_port('[::]:' + port)
server.start()
print("Server started on port " + port)

# Start the simulated client
with grpc.insecure_channel(f'localhost:{port}') as channel:
    stub = chatroom_pb2_grpc.ChatRoomStub(channel)
    
    # Test user creation and when username already exists
    assert chatroom_client.CreateUser(stub, "user1", "pass1", test=True) == (True, "User user1 created successfully")
    assert chatroom_client.CreateUser(stub, "user1", "pass1", test=True) == (False, "Username already exists")

    # Test login and when user already logged in
    assert chatroom_client.Login(stub, status=None, username="user1", password="pass1", test=True) == (True, "User user1 login successful", "user1")
    assert chatroom_client.Login(stub, status=None, username="user1", password="pass1", test=True) == (False, "User user1 is already online")

    # Test logout and when user is not logged in
    assert chatroom_client.Logout(stub, status="user1", test=True) == (True, "User user1 logged out successfully", None)
    assert chatroom_client.Logout(stub, status="user1", test=True) == (False, "User user1 is already offline")

    # Test login when password is wrong and when user does not exist
    assert chatroom_client.Login(stub, status=None, username="user1", password="pass2", test=True) == (False, "Incorrect password for user user1")
    assert chatroom_client.Login(stub, status=None, username="user2", password="pass1", test=True) == (False, "User user2 does not exist")

    # Test list users
    chatroom_client.CreateUser(stub, "user2", "pass2", test=True)
    chatroom_client.CreateUser(stub, "user123", "pass123", test=True)
    chatroom_client.CreateUser(stub, "usurper1", "pass123", test=True)
    chatroom_client.CreateUser(stub, "person1", "pass1", test=True)
    chatroom_client.CreateUser(stub, "person2", "pass2", test=True)

    assert chatroom_client.ListUsers(stub, partial="", test=True) == (True, "user1 user2 user123 usurper1 person1 person2")
    assert chatroom_client.ListUsers(stub, partial="us", test=True) == (True, "user1 user2 user123 usurper1")
    assert chatroom_client.ListUsers(stub, partial="user", test=True) == (True, "user1 user2 user123")
    assert chatroom_client.ListUsers(stub, partial="user1", test=True) == (True, "user1 user123")
    assert chatroom_client.ListUsers(stub, partial="person", test=True) == (True, "person1 person2")
    assert chatroom_client.ListUsers(stub, partial="individual", test=True) == (False, "No matching users found")

    # Test delete user
    assert chatroom_client.DeleteUser(stub, status="person1", cnfm_username="person1", test=True) == (False, "User person1 is offline, cannot delete")
    chatroom_client.Login(stub, status=None, username="person1", password="pass1", test=True)
    assert chatroom_client.DeleteUser(stub, status="person1", cnfm_username="person1", test=True) == (True, "User person1 deleted successfully", None)
    assert chatroom_client.DeleteUser(stub, status="person1", cnfm_username="person1", test=True) == (False, "User person1 does not exist") # this case is actually blocked by client-side logic normally
    assert chatroom_client.ListUsers(stub, partial="pe", test=True) == (True, "person2")

    # Test send message
    chatroom_client.Login(stub, status=None, username="user1", password="pass1", test=True)
    chatroom_client.Login(stub, status=None, username="user2", password="pass2", test=True)
    chatroom_client.Login(stub, status=None, username="user123", password="pass123", test=True)
    chatroom_client.Login(stub, status=None, username="usurper1", password="pass123", test=True)
    chatroom_client.Login(stub, status=None, username="person2", password="pass2", test=True)

    # Send message to online and then offline and then nonexistent user
    assert chatroom_client.SendMessage(stub, status="user1", receiverusername="user2", message="Hello user2", test=True) == (True, "User user2 is online, message sent successfully")
    time.sleep(3) # wait for message to be received
    chatroom_client.Logout(stub, status="user2", test=True)
    assert chatroom_client.SendMessage(stub, status="user1", receiverusername="user2", message="Hello user2 again", test=True) == (True, "User user2 is offline, message queued")
    assert chatroom_client.SendMessage(stub, status="user1", receiverusername="user3", message="Hello user3", test=True) == (False, "User user3 does not exist")
    
    # user2 logs back in and receives the message
    assert chatroom_client.Login(stub, status=None, username="user2", password="pass2", test="relogin") == "user1 says: Hello user2 again"

server.stop(grace=None)

print("All tests passed!")