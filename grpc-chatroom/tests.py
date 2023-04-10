import sys
import chatroom_client
import grpc
import chatroom_pb2_grpc
from chatroom_server import ChatRoom
from concurrent import futures

port = '50054'
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
chatroom_pb2_grpc.add_ChatRoomServicer_to_server(ChatRoom(), server)
server.add_insecure_port('[::]:' + port)
server.start()
print("Server started on port " + port)

chatroom_client.CreateUser(server)

server.wait_for_termination()