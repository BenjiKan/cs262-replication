from concurrent import futures
#import logging

import grpc
import chatroom_pb2
import chatroom_pb2_grpc

import time
import threading
import re

import socket

import os
import constants
import signal
import sys

import json
from google.protobuf.json_format import MessageToJson, Parse

#############
##### Print which process is printing too
#############
my_pid = os.getpid()
IDNT = ""

class tempCallObj():
    def info(self, *values, sep='', end='\n', file=sys.stdout, flush=False):
        print(*values, sep = sep, end = end, file = file, flush = flush)
    def basicConfig(self, *args, **kwargs):
        return
logging = tempCallObj()
# logging.info("Testing", end = "   End\n")

#######################################
#### CODE FOR GRPC CHATROOM SERVER ####
#######################################
class ChatRoom(chatroom_pb2_grpc.ChatRoomServicer):
    user_passwords = {} # list of users in {username: password} form
    messages = {} # list of pending messages in {username: [messages]} form
    user_is_online = {} # list of users with boolean flag for online status {username: True/False}
    lock = threading.Lock() # lock for messages
    log_lock = threading.Lock() # lock for internal log
    internal_log = []

    def __init__(self, leader_port, is_leader):
        self.leader_port = leader_port
        self.is_leader = is_leader

    def CreateUser(self, request, context):
        """
        Creates a new user with the given username and password.
        """
        self.log_lock.acquire()
        new_cmd = ("CreateUser", MessageToJson(request))
        self.internal_log.append(new_cmd)
        self.log_lock.release()
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
        print(f"{IDNT}[{my_pid}] " + "Users: ", self.user_passwords.keys())
        # print(self.port) <<< MM: This won't work. Will delete and refactor.
        return chatroom_pb2.requestReply(status=1, message=f"User {username} created successfully")

    def Login(self, request, context):
        """
        Logs in the user with the given username and password.
        """
        self.log_lock.acquire()
        new_cmd = ("Login", MessageToJson(request))
        self.internal_log.append(new_cmd)
        self.log_lock.release()
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
            print(f"{IDNT}[{my_pid}] " + username + " logged in")
            return chatroom_pb2.requestReply(status=1, message="Login successful")

    def Logout(self, request, context):
        """
        Logs out the user with the given username.
        """
        self.log_lock.acquire()
        new_cmd = ("Logout", MessageToJson(request))
        self.internal_log.append(new_cmd)
        self.log_lock.release()
        username = request.username
        if username not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        elif not self.user_is_online[username]:
            return chatroom_pb2.requestReply(status=0, message="User is already offline")
        else:
            self.lock.acquire()
            self.user_is_online[username] = False
            self.lock.release()
            print(f"{IDNT}[{my_pid}] " + username + " logged out")
            return chatroom_pb2.requestReply(status=1, message="Logout successful")

    def ListUsers(self, request, context):
        """
        Lists all users matching prefix provided, or lists all users.
        """
        self.log_lock.acquire()
        new_cmd = ("ListUsers", MessageToJson(request))
        self.internal_log.append(new_cmd)
        self.log_lock.release()
        if request.partialusername == "":
            print(f"{IDNT}[{my_pid}] " + "Returning all users")
            return chatroom_pb2.requestReply(status=1, message=" ".join(self.user_passwords.keys()))
        else:
            partial = re.compile(request.partialusername)
            matching_users = []
            print(f"{IDNT}[{my_pid}] " + "Returning user(s) starting with " + request.partialusername)
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
        self.log_lock.acquire()
        new_cmd = ("DeleteUser", MessageToJson(request))
        self.internal_log.append(new_cmd)
        self.log_lock.release()
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
            print(f"{IDNT}[{my_pid}] " + "Deleted user " + username + " successfully")
            print(f"{IDNT}[{my_pid}] " + "Users: ", self.user_passwords.keys())
            return chatroom_pb2.requestReply(status=1, message="User deleted successfully")

    def SendMessage(self, request, context):
        """
        Sends a message to the given user.
        """
        self.log_lock.acquire()
        new_cmd = ("SendMessage", MessageToJson(request))
        self.internal_log.append(new_cmd)
        self.log_lock.release()
        senderusername = request.senderusername
        receiverusername = request.receiverusername
        message = "\033[92m" + senderusername + "\033[0m" + " says: " + request.message # embed sender username in message
        if receiverusername not in self.user_passwords:
            return chatroom_pb2.requestReply(status=0, message="Username does not exist")
        # if user is offline, queue message
        if not self.user_is_online[receiverusername]:
            self.lock.acquire()
            self.messages[receiverusername].append(message)
            self.lock.release()    
            print(f"{IDNT}[{my_pid}] " + "Queuing message for user %s: \"%s\"" % (receiverusername, message))
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
        logging.info(f"IncomingStream called for user {request.username}")

        username = request.username
        try: 
            # if user is online, send messages
            while self.user_is_online[username]:
                while len(self.messages[username]) > 0: # if pending messages
                    self.lock.acquire()
                    message = self.messages[username].pop(0)
                    self.lock.release()
                    print(f"{IDNT}[{my_pid}] " + "Sending message to user %s: \"%s\"" % (username, message))
                    self.log_lock.acquire()
                    new_cmd = ("release_message", username)
                    self.internal_log.append(new_cmd)
                    self.log_lock.release()
                    yield chatroom_pb2.Message(senderusername="", receiverusername=username, message=message)
                time.sleep(0.1)
            logging.info(f"Stream closed for user {request.username}")
        except: 
            # catch errors immediately after an account is deleted
            print(f"{IDNT}[{my_pid}] " + "no stream")
    
    def srv_GetNewChanges(self, request, context):
        """
        Used by backup to request new changes from leader. Each backup opens one
        for each machine higher up in the hierarchy
        """
        # logging.info(f"Internal steram opened for server")
        try:
            for cmd in self.internal_log:
                nxt = chatroom_pb2.internalRequest()
                nxt.command_type, nxt.params = cmd
                yield nxt
        except Exception as exn:
            print(f"{IDNT}[{my_pid}] getNewChanges exception {exn}")
    
    def srv_CheckLeader(self, request, context):
        print(f"[{my_pid}] CHECKLEADER CALLED, RETURNING", self.is_leader, self.leader_port)
        return chatroom_pb2.requestReply(status = self.is_leader, message=str(self.is_leader) + " | " + str(self.leader_port))

    def srv_ElectLeader(self, request, context):
        return super().srv_ElectLeader(request, context)

    def release_msg(self, username):
        self.lock.acquire()
        message = self.messages[username].pop(0)
        self.lock.release()

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
    def __init__(self, host, port, leader_port, is_leader):
        self.host = host
        self.port = port
        self.processed_cmds = []
        self.ldrp, self.isl = leader_port, is_leader
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.chatroom = ChatRoom(leader_port, is_leader)
        chatroom_pb2_grpc.add_ChatRoomServicer_to_server(self.chatroom, self.server)
        self.server.add_insecure_port('[::]:' + self.port)
        self.main_stub = None
    
    def start_server(self):
        self.server.start()
        print(f"{IDNT}[{my_pid}] " + "Server started on port " + self.port + " with leader " + self.chatroom.leader_port + 
              f" | Currently is{'' if self.chatroom.is_leader else ' not'} leader")
        
        self.main_channel = grpc.insecure_channel(f"{self.host}:{self.port}")
        self.main_stub = chatroom_pb2_grpc.ChatRoomStub(self.main_channel)
        self.run_loop()
        self.server.wait_for_termination()

    def run_cmd(self, cmd):
        command_type, params = cmd.command_type, cmd.params
        if command_type == "CreateUser":
            request = Parse(params, chatroom_pb2.User())
            self.main_stub.CreateUser(request)
        elif command_type == "Login":
            request = Parse(params, chatroom_pb2.User())
            self.main_stub.Login(request)
        elif command_type == "Logout":
            request = Parse(params, chatroom_pb2.User())
            self.main_stub.Logout(request)
        elif command_type == "ListUsers":
            request = Parse(params, chatroom_pb2.UserList())
            self.main_stub.ListUsers(request)
        elif command_type == "DeleteUser":
            request = Parse(params, chatroom_pb2.User())
            self.main_stub.DeleteUser(request)
        elif command_type == "SendMessage":
            request = Parse(params, chatroom_pb2.Message())
            self.main_stub.SendMessage(request)
        elif command_type == "release_message":
            username = params
            self.main_stub.release_msg(username)
        else:
            print("Bad command", command_type)
    
    def run_loop(self):
        while True:
            if self.port == self.chatroom.leader_port:
                # print(f"{IDNT}[{my_pid}] " + "Running as lead server")
                pass
            else:
                # Establish connection to primary server and get commits
                try:
                    with grpc.insecure_channel(f"{self.host}:{self.chatroom.leader_port}") as bckp_channel:
                        stub = chatroom_pb2_grpc.ChatRoomStub(bckp_channel)
                        res = stub.srv_CheckLeader(chatroom_pb2.Empty())
                        if res.status:
                            print(f"{IDNT}[{my_pid}] " + "\033[92mConnected to leader\033[0m")
                            while True:
                                res_log = stub.srv_GetNewChanges(chatroom_pb2.Empty())
                                for entry in res_log:
                                    if not entry in self.processed_cmds:
                                        print("Adding", entry)
                                        self.processed_cmds.append(entry)
                                        self.run_cmd(entry)
                                pass
                        else:
                            pass
                except grpc._channel._InactiveRpcError as inactive_exn:
                    print(f"{IDNT}[{my_pid}] " + f"\033[91mServer at port {self.chatroom.leader_port} is unavailable\033[0m")
                    print(inactive_exn.details)
                    # Run leader election here
                    avail_ports = []
                    for i in constants.SERVER_PORTS:
                        try:
                            with grpc.insecure_channel(f"{self.host}:{i}") as chnl:
                                stub = chatroom_pb2_grpc.ChatRoomStub(chnl)
                                res = stub.srv_CheckLeader(chatroom_pb2.Empty())
                                avail_ports.append(i)
                        except grpc._channel._InactiveRpcError as inactive_exn:
                            continue
                    self.chatroom.leader_port = str(min(avail_ports))
                    self.chatroom.is_leader = self.port == self.chatroom.leader_port
                    print("\033[91mNEW: ", avail_ports, self.chatroom.leader_port, self.chatroom.is_leader)
                    print("\033[0m")
                except Exception as e:
                    print(f"{IDNT}[{my_pid}] Ran into exception {e}")

#############################################
#### CODE FOR LAUNCHING SERVER INSTANCES ####
#############################################
import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("-s", "--server_num", type=int, default=0, help="Server index (0-2)")
def serve():
    """
    Starts server given CLI argument
    """
    args = argParser.parse_args()
    global my_pid
    print(f"\033[92m[{my_pid}]\033[0m Starting server...")
    print(f"\033[92m[{my_pid}]\033[0m " + "Host:", socket.gethostbyname(socket.gethostname()))
    print(f"\033[92m[{my_pid}]\033[0m " + "Copy the above in the client to connect to the server.")

    HOST = socket.gethostbyname(socket.gethostname())
    server_obj = ServerObject(HOST, str(constants.SERVER_PORTS[args.server_num]), str(constants.SERVER_PORTS[0]), args.server_num == 0)
    # server_obj.server.leader_port = str(constants.SERVER_PORTS[0])
    # server_obj.server.is_leader = args.server_num == 0
    # print(server_obj.server.leader_port, server_obj.server.is_leader)
    server_obj.start_server()


def serve_old():
    """
    Starts the server.
    """

    # TODO: start up 3 parallel server processes on different ports, and have the client connect to one of them
    # mutually connect the 3 servers so that they can all send messages to each other
 
    global IDNT, my_pid

    print(f"{IDNT}[{my_pid}] " + "Starting server...")
    print(f"{IDNT}[{my_pid}] " + "Host:", socket.gethostbyname(socket.gethostname()))
    print(f"{IDNT}[{my_pid}] " + "Copy the above in the client to connect to the server.")

    HOST = socket.gethostbyname(socket.gethostname())
    N_SERVERS = 3
    servers = [ServerObject(HOST, str(constants.SERVER_PORTS[i])) for i in range(N_SERVERS)]

    child_pids = [0 for i in range(N_SERVERS)]
    for i in range(N_SERVERS):
        n = os.fork()
        if n == 0:
            if (os.getpid() != my_pid):
                IDNT = "    "
            my_pid = os.getpid()
            ########################
            ### Construct inter-server communications, then start client server ###
            def signal_exit_handler(*args):
                print(f"{IDNT}[{my_pid}] " + f"Exiting on pid {os.getpid()}")
                #### Do cleanups here
                sys.exit(0)
            signal.signal(signal.SIGTERM, signal_exit_handler)

            # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # s.bind((HOST, constants.INTERNAL_PORTS[i]))
            # s.listen(5)
            # time.sleep(0.5)
            # other_sockets = [None for i in range(N_SERVERS)]
            # for j in range(N_SERVERS):
            #     if j == i: continue
                
            #         # Do stu


            # Initialize first server as leader
            servers[i].server.leader_port = str(constants.SERVER_PORTS[0])
            servers[i].server.is_leader = i == 0
            servers[i].start_server()

            print(f"{IDNT}[{my_pid}] " + f"Server {i} started")

            # time.sleep(5)
            # servers[i].run_loop()
        else:
            child_pids[i] = n
            print(f"{IDNT}[{my_pid}] " + f"Parent: server idx {i} can, pid {child_pids[i]}")
    
    num_killed = 0
    server_alive = [True for i in range(N_SERVERS)]
    while num_killed < N_SERVERS - 1:
        print(f"{IDNT}[{my_pid}] " + "Press Ctrl-D to exit a thread")
        try:
            input()
        except EOFError:
            print(f"RECEIVED AT PID {os.getpid()}")
            prompt_choices = map(lambda x: str(x[0]),
                                 filter(lambda x: x[1], enumerate(server_alive)))
            idx = input(f"[{my_pid}] Which server to kill? (Alive: {'/'.join(prompt_choices)})")
            idx = int(idx.strip())
            try:
                if not server_alive[idx]: continue
                server_alive[idx] = False
                os.kill(child_pids[idx], signal.SIGTERM)
                num_killed += 1
                print(f"{IDNT}[{my_pid}] {num_killed} fault(s) reached!")
            except IndexError:
                continue


    # port = '50054'
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # chatroom_pb2_grpc.add_ChatRoomServicer_to_server(ChatRoom(), server)
    # server.add_insecure_port('[::]:' + port)
    # server.start()
    # print("Server started on port " + port)
    # server.wait_for_termination()
    while True:
        pass

if __name__ == '__main__':
    logging.basicConfig()
    serve()