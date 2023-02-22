from concurrent import futures
import logging

import grpc
import chatroom_pb2
import chatroom_pb2_grpc

import time
import threading
import re

# import constants
# from ..constants import *

class ChatRoom(chatroom_pb2_grpc.ChatRoomServicer):
    user_passwords = {} # username: password
    messages = {} # username: [messages]
    lock = threading.Lock() # lock for messages

    def CreateUser(self, request, context):
        """
        Creates a new user with the given username and password.
        """
        username = request.username
        password = request.password
        # cnfm_pw = request.cnfm_pw
        if username in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username already exists")
        # if password != cnfm_pw:
        #     return chatroom_pb2.CreateUserResponse(status=0, message="Passwords do not match")
        
        # if no problems, make account
        self.lock.acquire()
        self.user_passwords[username] = password
        self.messages[username] = []
        print(self.user_passwords.keys())
        self.lock.release()
        return chatroom_pb2.requestReply(status=1, message="User created successfully")

    def Login(self, request, context):
        """
        Logs in the user with the given username and password.
        """
        username = request.username
        password = request.password
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        if self.user_passwords[username] != password:
            return chatroom_pb2.requestReply(status=0, message="Incorrect password")
        return chatroom_pb2.requestReply(status=1, message="Login successful")

    def ListUsers(self, request, context):
        """
        Lists all users.
        """
        if request.partialusername == "":
            print("All users")
            return chatroom_pb2.requestReply(status=1, message=" ".join(self.user_passwords.keys()))
        else:
            partial = re.compile(request.partialusername)
            matching_users = []
            print("Matching users...")
            for username in self.user_passwords.keys():
                if partial.match(username):
                    matching_users.append(username)
            if len(matching_users) == 0:
                return chatroom_pb2.requestReply(status=0, message="No matching users")
            else:
                return chatroom_pb2.requestReply(status=1, message=" ".join(matching_users))
        
    ## TODO
    def DeleteUser(self, request, context):
        """
        Deletes the user with the given username.
        """
        username = request.username
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        self.lock.acquire()
        del self.user_passwords[username]
        del self.messages[username]
        self.lock.release()
        return chatroom_pb2.requestReply(status=1, message="User deleted successfully")

    def SendMessage(self, request, context):
        """
        Sends a message to the given user.
        """
        username = request.username
        message = request.message
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        self.lock.acquire()
        self.messages[username].append(message)
        self.lock.release()
        return chatroom_pb2.requestReply(status=1, message="Message sent successfully")

    def ReceiveMessage(self, request, context):
        """
        Receives a message from the given user.
        """
        username = request.username
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        while True:
            self.lock.acquire()
            if len(self.messages[username]) > 0:
                message = self.messages[username].pop(0)
                self.lock.release()
                yield chatroom_pb2.requestReply(status=1, message=message)
            else:
                self.lock.release()
                time.sleep(0.1)
    
    
def serve():
    """
    Starts the server.
    """
    port = '50054'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatroom_pb2_grpc.add_ChatRoomServicer_to_server(ChatRoom(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started on port " + port)
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
