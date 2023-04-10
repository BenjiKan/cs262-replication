import logging

import grpc
import chatroom_pb2
import chatroom_pb2_grpc

import threading

import time
from inputimeout import inputimeout, TimeoutOccurred
import sys
import constants

import signal # signal handler for SIGTERM

TIMEOUT = 60 # seconds before auto-log out
# handles the last pending request from the client
pending_request = {}

def CreateUser(stub, username=None, password=None, test=False):
    """
    Creates a new user with the given username and password.
    """
    global pending_request
    if username is None: username = input("Enter a username: ")
    if password is None: password = input("Enter a password: ")
    pending_request["username"] = username
    pending_request["password"] = password
    response = stub.CreateUser(chatroom_pb2.User(username=username, password=password))

    print(response.message)

    if test:
        return response.status, response.message

def Login(stub, status, username=None, password=None):
    """
    Logs in the user with the given username and password.
    """
    global pending_request
    if status!=None:
        print("You are already logged in as " + status + ". Please log out first.")
        return status
    if username is None: username = input("Enter a username: ")
    if password is None: password = input("Enter a password: ")
    pending_request["username"] = username
    pending_request["password"] = password
    response = stub.Login(chatroom_pb2.User(username=username, password=password))
    print(response.message)
    if response.status==0:
        return None
    else:
        logged_in = username

        # Start a thread to check for messages
        listening = stub.IncomingStream(chatroom_pb2.User(username=logged_in))
        threading.Thread(target=CheckMessages, daemon=True, args=(stub, logged_in, listening)).start()

        return logged_in


def recreate_thread(stub):
    global global_logged_in
    # Start a thread to check for messages
    listening = stub.IncomingStream(chatroom_pb2.User(username=global_logged_in))
    threading.Thread(target=CheckMessages, daemon=True, args=(stub, global_logged_in, listening)).start()

def Logout(stub, status):
    """
    Logs out the user with the given username.
    """
    global pending_request
    if status==None:
        print("Currently not logged in.")
        return status
    global global_logged_in
    if not global_logged_in is None:
        recreate_thread(stub)
    response = stub.Logout(chatroom_pb2.User(username=status))
    print(response.message)
    if response.status==1:
        logged_in = None
        return logged_in

def ListUsers(stub, partial=None):
    """
    Lists all users in the server. No need for login.
    """
    global global_logged_in
    if not global_logged_in is None:
        recreate_thread(stub)
    global pending_request
    if partial is None: partial = input("Enter a partial username (press enter if you want to see all users): ")
    pending_request['partial'] = partial
    if len(partial) == 0:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=""))
    else:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=partial))
    print(response.message)

def DeleteUser(stub, status, cnfm_username=None):
    """
    Deletes the user with the given username.
    """
    global pending_request
    # must be logged in to delete
    if status==None:
        print("You are not logged in.") 
        return status
    global global_logged_in
    if not global_logged_in is None:
        recreate_thread(stub)
    if cnfm_username is None: cnfm_username = input("Type your username if you are sure you want to delete this account: ")
    pending_request["cnfm_username"] = cnfm_username
    if cnfm_username != status:
        print("Username does not match.")
        return status
    else:
        response = stub.DeleteUser(chatroom_pb2.User(username=status))
        print(response.message)
        if response.status==1:
            logged_in = None
            return logged_in

def SendMessage(stub, status, receiverusername=None):
    """
    Sends a message from the logged in user to the given user.
    """
    global pending_request
    if status==None:
        print("You are not logged in.")
        return status
    global global_logged_in
    if not global_logged_in is None:
        recreate_thread(stub)
    if receiverusername is None: receiverusername = input("Enter the username you want to send to: ")
    pending_request['receiverusername'] = receiverusername
    if receiverusername == status:
        print("You cannot send messages to yourself.")
        return status
    message = input("Enter a message: ")
    response = stub.SendMessage(chatroom_pb2.Message(senderusername=status, receiverusername=receiverusername, message=message))
    print(response.message)

def CheckMessages(stub, status, listening):
    """
    Checks for messages from the logged in user. Called by thread in background.
    """
    if status==None:
        print("You are not logged in.")
        return status
    try:
        for message in listening: 
            print("\n"+message.message)
    except: # if account is deleted, no error.
        print("no listening found. break")
    return


global_logged_in = None
cur_channel = None
cur_stub = None
def run():
    """
    Main function to run the client.
    """

    global global_logged_in, cur_channel, cur_stub, pending_request

    # Connect to server
    # input host
    host = input("Enter the host address (or ENTER for 'localhost'): ")
    if host=="":
        host = "localhost"
    
    # port = 50054

    SERVER_PORT_IDX = 0
    while SERVER_PORT_IDX < constants.N_SERVER_PORTS:
        port = constants.SERVER_PORTS[SERVER_PORT_IDX]
        #port = constants.SERVER_PORTS[int(input("Input (0,1,2): ").strip())]

        print(f"Connecting to server at {host}:{port}...")
        
        # Handle pending request from last failed client request (i.e. server is down, switching)
        print("Login status:", global_logged_in)
        if len(pending_request) > 0:
            with grpc.insecure_channel(f"{host}:{port}") as channel:
                cur_channel = channel
                stub = chatroom_pb2_grpc.ChatRoomStub(channel)
                cur_channel, cur_stub = channel, stub

                try:
                    request = pending_request['request']
                    if request == "quit":
                        print("Trying to quit...")
                        if global_logged_in != None:
                            print("Logging out before quitting...")
                            global_logged_in = Logout(stub, status=global_logged_in)
                        sys.exit(0)
                        break
                    elif request == "help":
                        print("_________Commands___________")
                        print("help: print this menu")
                        print("create: create a new user")
                        print("login: log in to an existing user")
                        print("logout: log out of the current user")
                        print("list: list all users")
                        print("delete: delete the current user")
                        print("send: send a message to another user")
                        # print("check: check for incoming messages")
                        print("quit: quit the program")
                    elif request == "create":
                        print("Retrying create with",
                              f"username: {pending_request['username']}",
                              f"password: {pending_request['password']}" + "...", sep = '\n')
                        CreateUser(stub, username=pending_request["username"],
                                         password=pending_request['password'])
                    elif request == "login":
                        print("Retrying login with",
                              f"username: {pending_request['username']}",
                              f"password: {pending_request['password']}" + "...", sep = '\n')
                        global_logged_in = Login(stub, status=global_logged_in,
                                                       username=pending_request['username'],
                                                       password=pending_request["password"])
                    elif request == "logout":
                        print("Retrying logout...")
                        global_logged_in = Logout(stub, status=global_logged_in)
                    elif request == "list":
                        print("Retrying list with",
                              f"partial username: {pending_request['partial']}" + "...", sep = '\n')
                        ListUsers(stub, partial=pending_request["partial"])
                    elif request == "delete":
                        print("Retrying delete with",
                              f"confirm username: {pending_request['cnfm_username']}" + "...", sep = '\n')
                        global_logged_in = DeleteUser(stub, status=global_logged_in,
                                                            cnfm_username=pending_request["cnfm_username"])
                    elif request == "send":
                        print("Retrying send with",
                              f"recipient: {pending_request['receiverusername']}" + "...", sep = '\n')
                        SendMessage(stub, status=global_logged_in, receiverusername=pending_request["receiverusername"])
                    # elif request == "check": 
                    #     # can be private function, as this is done in the background. some users feel the need to manually refresh though
                    #     print("Retrying check...")
                    #     CheckMessages(stub, status=global_logged_in, listening=stub.IncomingStream(chatroom_pb2.User(username=global_logged_in)))
                    else:
                        print("Invalid command, try again.")
                except grpc._channel._InactiveRpcError as inactive_exn:
                    print(f"Host on port {port} is unavailable. Status: ", inactive_exn)
                    print("Switching hosts...")
                    SERVER_PORT_IDX += 1
                    continue
                except Exception as exn:
                    print("Exited from reconnect with non-timeout exception. See below:")
                    print(exn)
                    break

        # Begin main loop of connection
        with grpc.insecure_channel(f"{host}:{port}") as channel:
            cur_channel = channel
            stub = chatroom_pb2_grpc.ChatRoomStub(channel)
            # global_logged_in = None # username if logged in
            cur_channel, cur_stub = channel, stub

            try:
                while True:
                    # Print command prompt with username if logged in
                    if global_logged_in==None:
                        print("\nYou are not logged in.")
                    else:
                        print("\nYou are logged in as " + "\033[92m" + global_logged_in + "\033[0m")
                    # Get user input
                    try:
                        request = inputimeout(prompt="Enter a command (or \"help\"): ", timeout=TIMEOUT) 
                    except TimeoutOccurred:
                        # If no user input for TIMEOUT seconds, log out and prompt again
                        if global_logged_in!=None:
                            print("Timed out, logging out...")
                            pending_request['request'] = "logout"
                            global_logged_in = Logout(stub, status=global_logged_in)
                        continue
                    pending_request['request'] = request

                    # Menu of possible commands
                    if request == "quit":
                        if global_logged_in != None:
                            print("Logging out before quitting...")
                            global_logged_in = Logout(stub, status=global_logged_in)
                        sys.exit(0)
                        break
                    elif request == "help":
                        print("_________Commands___________")
                        print("help: print this menu")
                        print("create: create a new user")
                        print("login: log in to an existing user")
                        print("logout: log out of the current user")
                        print("list: list all users")
                        print("delete: delete the current user")
                        print("send: send a message to another user")
                        # print("check: check for incoming messages")
                        print("quit: quit the program")
                    elif request == "create":
                        CreateUser(stub)
                    elif request == "login":
                        global_logged_in = Login(stub, status=global_logged_in)
                    elif request == "logout":
                        global_logged_in = Logout(stub, status=global_logged_in)
                    elif request == "list":
                        ListUsers(stub)
                    elif request == "delete":
                        global_logged_in = DeleteUser(stub, status=global_logged_in)
                    elif request == "send":
                        SendMessage(stub, status=global_logged_in)
                    # elif request == "check": 
                    #     # can be private function, as this is done in the background. some users feel the need to manually refresh though
                    #     CheckMessages(stub, status=global_logged_in, listening=stub.IncomingStream(chatroom_pb2.User(username=global_logged_in)))
                    else:
                        print("Invalid command, try again.")
            except grpc._channel._InactiveRpcError as inactive_exn:
                print("Host is unavailable. Status: ", inactive_exn)
                print("Switching hosts...")
            except Exception as exn:
                print("Exited with non-timeout exception. See below:")
                print(exn)
                break
        SERVER_PORT_IDX += 1



if __name__ == '__main__':
    # This ensures that if the client dies, we don't have zombie logins
    def received_SIG_TO_EXIT(*args, **kwargs):
        global global_logged_in, cur_channel, cur_stub
        print(f"RECEIVED SIGNAL {args[0]}. Exiting.")
        # print(f"Args received: {args}")
        # print(f"Kwargs received: {kwargs}")
        print(global_logged_in, cur_channel, cur_stub)
        if not (global_logged_in is None):
            assert (not (cur_stub is None)), "cur_stub check failed"
            assert (not (cur_channel is None)), "cur_channel check failed"
            global_logged_in = Logout(cur_stub, status=global_logged_in)
        sys.exit(0)
    signal.signal(signal.SIGINT, received_SIG_TO_EXIT) # KeyboardInterrupt
    signal.signal(signal.SIGTERM, received_SIG_TO_EXIT) # kill via terminal
    logging.basicConfig()
    try:
        run()
    except EOFError:
        received_SIG_TO_EXIT("EOFERROR")