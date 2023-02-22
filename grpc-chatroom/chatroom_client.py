import logging

import grpc
import chatroom_pb2
import chatroom_pb2_grpc

import time
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

def Login(stub):
    username = input("Enter a username: ")
    password = input("Enter a password: ")
    response = stub.Login(chatroom_pb2.User(username=username, password=password))
    print(response.message)

def ListUsers(stub):
    partial = input("Enter a partial username: ")
    if len(partial) == 0:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=""))
    else:
        response = stub.ListUsers(chatroom_pb2.UserList(partialusername=partial))
    print(response.message)

def run():
    with grpc.insecure_channel('localhost:50054') as channel:
        stub = chatroom_pb2_grpc.ChatRoomStub(channel)

        while True:
            request = input("Enter a command: ")
            if request == "quit":
                # add if logged in
                sys.exit(0)
                break
            elif request == "create":
                CreateUser(stub)
            elif request == "login":
                Login(stub)
            elif request == "list":
                ListUsers(stub)
            else:
                print("Invalid command, try again.")
        

if __name__ == '__main__':
    logging.basicConfig()
    run()