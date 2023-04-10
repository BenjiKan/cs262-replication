from concurrent import futures
import logging

import grpc
import chatroom_pb2
import chatroom_pb2_grpc

import time
import threading
import re

import socket

import os
import constants

#######################################
#### CODE FOR GRPC CHATROOM SERVER ####
#######################################
class ChatRoom(chatroom_pb2_grpc.ChatRoomServicer):
    user_passwords = {} # list of users in {username: password} form
    messages = {} # list of pending messages in {username: [messages]} form
    user_is_online = {} # list of users with boolean flag for online status {username: True/False}
    lock = threading.Lock() # lock for messages

    def CreateUser(self, request, context):
        """
        Creates a new user with the given username and password.
        """
        username = request.username
        password = request.password
        if username in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username already exists")
        
        # if no problems, make account
        self.lock.acquire()
        self.user_passwords[username] = password
        self.messages[username] = []
        self.user_is_online[username] = False
        self.lock.release()
        print("Users: ", self.user_passwords.keys())
        # print(self.port) <<< MM: This won't work. Will delete and refactor.
        return chatroom_pb2.requestReply(status=1, message="User created successfully")

    def Login(self, request, context):
        """
        Logs in the user with the given username and password.
        """
        username = request.username
        password = request.password
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        elif self.user_passwords[username] != password:
            return chatroom_pb2.requestReply(status=0, message="Incorrect password")
        elif self.user_is_online[username]:
            return chatroom_pb2.requestReply(status=0, message="User is already online")
        else:
            self.lock.acquire()
            self.user_is_online[username] = True
            self.lock.release()
            print(username + " logged in")
            return chatroom_pb2.requestReply(status=1, message="Login successful")

    def Logout(self, request, context):
        """
        Logs out the user with the given username.
        """
        username = request.username
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        elif not self.user_is_online[username]:
            return chatroom_pb2.requestReply(status=0, message="User is already offline")
        else:
            self.lock.acquire()
            self.user_is_online[username] = False
            self.lock.release()
            print(username + " logged out")
            return chatroom_pb2.requestReply(status=1, message="Logout successful")

    def ListUsers(self, request, context):
        """
        Lists all users matching prefix provided, or lists all users.
        """
        if request.partialusername == "":
            print("Returning all users")
            return chatroom_pb2.requestReply(status=1, message=" ".join(self.user_passwords.keys()))
        else:
            partial = re.compile(request.partialusername)
            matching_users = []
            print("Returning user(s) starting with " + request.partialusername)
            for username in self.user_passwords.keys():
                if partial.match(username):
                    matching_users.append(username)
            if len(matching_users) == 0:
                return chatroom_pb2.requestReply(status=0, message="No matching users")
            else:
                return chatroom_pb2.requestReply(status=1, message=" ".join(matching_users))
        
    def DeleteUser(self, request, context):
        """
        Deletes the user with the given username.
        """
        username = request.username
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        elif not self.user_is_online[username]:
            return chatroom_pb2.requestReply(status=0, message="User is already offline")
        else:
            self.lock.acquire()
            del self.user_passwords[username]
            del self.messages[username]
            del self.user_is_online[username]
            self.lock.release()
            print("Deleted user " + username + " successfully")
            print("Users: ", self.user_passwords.keys())
            return chatroom_pb2.requestReply(status=1, message="User deleted successfully")

    def SendMessage(self, request, context):
        """
        Sends a message to the given user.
        """
        senderusername = request.senderusername
        receiverusername = request.receiverusername
        message = senderusername + " says: " + request.message # embed sender username in message
        if receiverusername not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        # if user is offline, queue message
        if not self.user_is_online[receiverusername]:
            self.lock.acquire()
            self.messages[receiverusername].append(message)
            self.lock.release()    
            print("Queuing message for user %s: \"%s\"" % (receiverusername, message))
            return chatroom_pb2.requestReply(status=1, message="User %s is offline, message queued" % (receiverusername))
        # if user is online, send message
        else:
            self.lock.acquire()
            self.messages[receiverusername].append(message)
            self.lock.release()
            return chatroom_pb2.requestReply(status=1, message="User %s is online, message sent" % (receiverusername))

    def IncomingStream(self, request, context):
        """
        Sends a response-stream of incoming messages to the given user.
        Each client opens this and waits for server to send them messages. 
        """
        logging.info("IncomingStream called for user %s", request.username)

        username = request.username
        try: 
            # if user is online, send messages
            while self.user_is_online[username]:
                while len(self.messages[username]) > 0: # if pending messages
                    message = self.messages[username].pop(0)
                    print("Sending message to user %s: \"%s\"" % (username, message))
                    yield chatroom_pb2.Message(senderusername="", receiverusername=username, message=message)
                time.sleep(1)
        except: 
            # catch errors immediately after an account is deleted
            print("no stream")

    def log(host, port, op):
        """
        Updates the log file with the current state of the server.
        """
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # maybe save list of user/passwords database separately from logs of actions

        with open(f'logs/{host}_{port}.out', 'w') as f:
            # operations for log in, log out, send message, list users, delete user


            if op == "user":
                f.write("Users: " + str(server.user_passwords.keys()) + "")

            f.write("Users: " + str(server.user_passwords.keys()) + "")

            f.close()

        # eventually use this log function in each of the server functions


################################
#### CODE FOR SERVER OBJECT ####
################################

class ServerObject():
    def __init__(self, host, port):
        self.host = host
        self.port = port

#############################################
#### CODE FOR LAUNCHING SERVER INSTANCES ####
#############################################
def serve():
    """
    Starts the server.
    """

    # TODO: start up 3 parallel server processes on different ports, and have the client connect to one of them
    # mutually connect the 3 servers so that they can all send messages to each other
 

    print("Starting server...")
    print("Host:", socket.gethostbyname(socket.gethostname()))
    print("Copy the above in the client to connect to the server.")

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