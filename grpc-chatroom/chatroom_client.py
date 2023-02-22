import logging

import grpc
import chatroom_pb2
import chatroom_pb2_grpc

import threading

import time
from inputimeout import inputimeout
import sys

# import constants
# from constants import *



def CreateUser(stub):
    username = input("Enter a username: ")
    password = input("Enter a password: ")
    # cnfm_pw = input("Confirm password: ")
    # response = stub.CreateUser(chatroom_pb2.User(username=username, password=password, cnfm_pw=cnfm_pw))
    response = stub.CreateUser(chatroom_pb2.User(username=username, password=password))

    print(response.message)

def Login(stub, status):
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
    if status==None:
        print("You are not logged in.")
        return status
    response = stub.Logout(chatroom_pb2.User(username=status))
    print(response.message)
    if response.status==1:
        logged_in = None
        return logged_in

def ListUsers(stub):
    partial = input("Enter a partial username (press enter if you want to see all users): ")
    if len(partial) == 0:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=""))
    else:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=partial))
    print(response.message)

def DeleteUser(stub, status):
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
    if status==None:
        print("You are not logged in.")
        return status
    for message in listening: #stub.CheckMessages(chatroom_pb2.User(username=status)):
        print(message.message)

    
def run():
    with grpc.insecure_channel('localhost:50054') as channel:
        stub = chatroom_pb2_grpc.ChatRoomStub(channel)
        logged_in = None

        while True:
            if logged_in==None:
                print("\nYou are not logged in.")
            else:
                print("\nYou are logged in as " + logged_in)
            # request = input("Enter a command: ")
            try:
                request = inputimeout(prompt="Enter a command: ", timeout=10)
            except Exception:
                print("Timed out, checking for messages...")
                CheckMessages(stub, status=logged_in, listening=stub.IncomingStream(chatroom_pb2.User(username=logged_in)))
                continue


            if request == "quit":
                sys.exit(0)
                break
            elif request == "create":
                CreateUser(stub)
            elif request == "login":
                logged_in = Login(stub, status=logged_in)
            elif request == "logout":
                logged_in = Logout(stub, status=logged_in)
            elif request == "list":
                ListUsers(stub)
            elif request == "delete":
                logged_in = DeleteUser(stub, status=logged_in)
            elif request == "send":
                SendMessage(stub, status=logged_in)
            elif request == "check": # mostly obsolete, this is done in the background
                CheckMessages(stub, status=logged_in, listening=stub.IncomingStream(chatroom_pb2.User(username=logged_in)))
            else:
                print("Invalid command, try again.")

        

if __name__ == '__main__':
    logging.basicConfig()
    run()