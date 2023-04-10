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


    
    # Test CreateUser
    assert chatroom_client.CreateUser(stub, "user1", "pass1", test=True) == (True, "User user1 created successfully")
    assert chatroom_client.CreateUser(stub, "user1", "pass1", test=True) == (False, "Username already exists")




print("All tests passed!")

server.wait_for_termination()