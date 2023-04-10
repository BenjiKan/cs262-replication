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

def CreateUser(stub):
    """
    Creates a new user with the given username and password.
    """
    username = input("Enter a username: ")
    password = input("Enter a password: ")
    response = stub.CreateUser(chatroom_pb2.User(username=username, password=password))

    print(response.message)

def Login(stub, status):
    """
    Logs in the user with the given username and password.
    """
    if status!=None:
        print("You are already logged in as " + status + ". Please log out first.")
        return status
    username = input("Enter a username: ")
    password = input("Enter a password: ")
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


def Logout(stub, status):
    """
    Logs out the user with the given username.
    """
    if status==None:
        print("You are not logged in.")
        return status
    response = stub.Logout(chatroom_pb2.User(username=status))
    print(response.message)
    if response.status==1:
        logged_in = None
        return logged_in

def ListUsers(stub):
    """
    Lists all users in the server. No need for login.
    """
    partial = input("Enter a partial username (press enter if you want to see all users): ")
    if len(partial) == 0:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=""))
    else:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=partial))
    print(response.message)

def DeleteUser(stub, status):
    """
    Deletes the user with the given username.
    """
    # must be logged in to delete
    if status==None:
        print("You are not logged in.") 
        return status
    cnfm_username = input("Type your username if you are sure you want to delete this account: ")
    if cnfm_username != status:
        print("Username does not match.")
        return status
    else:
        response = stub.DeleteUser(chatroom_pb2.User(username=status))
        print(response.message)
        if response.status==1:
            logged_in = None
            return logged_in

def SendMessage(stub, status):
    """
    Sends a message from the logged in user to the given user.
    """
    if status==None:
        print("You are not logged in.")
        return status
    receiverusername = input("Enter the username you want to send to: ")
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

    global global_logged_in, cur_channel, cur_stub

    # Connect to server
    # input host
    host = input("Enter the host address (or ENTER for 'localhost'): ")
    if host=="":
        host = "localhost"
    
    # port = 50054

    SERVER_PORT_IDX = 0
    while SERVER_PORT_IDX < 1: #constants.N_SERVER_PORTS:
        port = constants.SERVER_PORTS[SERVER_PORT_IDX]
        port = constants.SERVER_PORTS[int(input("Input (0,1,2): ").strip())]

        print(f"Connecting to server at {host}:{port}...")
        
        # Begin main loop of connection
        with grpc.insecure_channel(f"{host}:{port}") as channel:
            cur_channel = channel
            stub = chatroom_pb2_grpc.ChatRoomStub(channel)
            global_logged_in = None # username if logged in
            cur_channel, cur_stub = channel, stub

            try:
                while True:
                    # Print command prompt with username if logged in
                    if global_logged_in==None:
                        print("\nYou are not logged in.")
                    else:
                        print("\nYou are logged in as " + global_logged_in)

                    # Get user input
                    try:
                        request = inputimeout(prompt="Enter a command (or \"help\"): ", timeout=TIMEOUT) 
                    except TimeoutOccurred:
                        # If no user input for TIMEOUT seconds, log out and prompt again
                        if global_logged_in!=None:
                            print("Timed out, logging out...")
                            global_logged_in = Logout(stub, status=global_logged_in)
                        continue

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
                        print("check: check for incoming messages")
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
                    elif request == "check": 
                        # can be private function, as this is done in the background. some users feel the need to manually refresh though
                        CheckMessages(stub, status=global_logged_in, listening=stub.IncomingStream(chatroom_pb2.User(username=global_logged_in)))
                    else:
                        print("Invalid command, try again.")
            except grpc._channel._InactiveRpcError as inactive_exn:
                print("Host is unavailable. Status: ", inactive_exn)
            except Exception as exn:
                print("Exited with non-timeout exception. See below:")
                print(exn)
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