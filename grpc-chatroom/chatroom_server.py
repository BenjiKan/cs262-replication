from concurrent import futures
import logging

import grpc
import chatroom_pb2
import chatroom_pb2_grpc

import time
import threading
import re

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
        elif self.user_passwords[username] != password:
            return chatroom_pb2.requestReply(status=0, message="Incorrect password")
        elif self.user_is_online[username]:
            return chatroom_pb2.requestReply(status=0, message="User is already online")
        else:
            self.lock.acquire()
            self.user_is_online[username] = True
            self.lock.release()
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
            return chatroom_pb2.requestReply(status=1, message="Logout successful")

    def ListUsers(self, request, context):
        """
        Lists all users.
        """
        if request.partialusername == "":
            print("Returning all users...")
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
            print(self.user_passwords.keys())
            self.lock.release()
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
                    print("Sending/queuing message to user %s: \"%s\"" % (username, message))
                    yield chatroom_pb2.Message(senderusername="", receiverusername=username, message=message)
                time.sleep(1)
        except: # catch errors after an account is deleted
            print("no stream")
    
    
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
