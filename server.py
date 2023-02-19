#Ref: https://www.geeksforgeeks.org/socket-programming-multi-threading-python/

# Imports
import socket
import sys
import os
# import mysql.connector
import random

 
# import thread module
from _thread import *
import threading

accountName_table={}
accountBalance_table={}

p_lock = threading.Lock()

# import constants
from constants import *


# thread function for BANK TRANSACTIONS
def threaded(c):
    while True:
        data_list=[]
        # data received from client
        data = c.recv(1024)
        data_str = data.decode('UTF-8')
        if not data:
            print('Bye')
            break
        print(data_str+"\n")
        #data_str = str(data)
        data_list = data_str.split('|')
        opcode = data_list[0]
        #opcode = opcode_b[2:]
        print("Opcode:" + str(opcode))

        if opcode == '1':
            #account creation
            accountID  = str(random.randint(0,1000))
            accountName_table[accountID] = str(data_list[1])
            accountBalance_table[accountID] = str(0)
            print("key: " + str(accountID) + "\n")
            data = "Account ID: " + str(accountID)+"\n"
        elif opcode == '2':
            #deposit money

            accountID = str(data_list[1])
            print("key: " + str(data_list[1]) + "\n")
            if accountID in accountName_table:
                print("key exists: " + str(accountID) + " old balance:"+  str(accountBalance_table[accountID]) + "\n")
                balance = accountBalance_table[accountID]
                accountBalance_table[accountID] = str(int(balance) + int(data_list[2]))
                data = "Account ID: " +  str(accountID) + " New Balance: "+  str(accountBalance_table[accountID]) +"\n"
            else:
                print("key doesnt exist: " + str(accountID)  + "\n")
                data = "Account ID: " +  str(accountID) + " doesn't exist \n"
        elif opcode == '3':
            #withdraw money
            accountID = str(data_list[1])
            print("key: " + str(data_list[1]) + "\n")
            if accountID in accountName_table:
                print("key exists: " + str(accountID) + " old balance:"+  str(accountBalance_table[accountID]) + "\n")
                balance = accountBalance_table[accountID]
                tempBalance = int(balance) - int(data_list[2])
                if tempBalance >0:
                    accountBalance_table[accountID] = str(tempBalance)
                    data = "Account ID: " +  str(accountID) + " New Balance: "+  str(accountBalance_table[accountID]) +"\n"
                else:
                    data = "Account ID: " +  str(accountID) + " balance too low!" + "\n"
            else:
                print("key doesnt exist: " + str(accountID)  + "\n")
                data = "Account ID: " +  str(accountID) + " doesn't exist \n"
        elif opcode == '4':
            #view balance
            accountID = data_list[1]
            data = "Account ID: " +  str(accountID) + " New Balance: " + str(accountBalance_table[accountID]) +"\n"
        else:
            data = "Invalid Request\n"

        # send back reversed string to client
        c.send(data.encode('ascii')) 
    # connection closed
    
    c.close()


# log in function
# logins in user if username and password are correct
# returns true if successful, false otherwise. Save as Global Variable
# for future operations, CHECK IF LOGGED IN, then do operations

# receive messages
# returns list of messages (with sender, timestamp) if successful, false otherwise

# send messages
# sends message to specified user if they exist

# log out function
# logs out user if successful, false otherwise

# delete account function
# deletes account if successful, false otherwise


class AccountHandler:
    def __init__(self, store = {}):
        self.account_list = store # username: password
        # username: currently online or not
        self.is_online = {usr: False for usr in self.account_list.keys()}
    
    def _create_account(self, username, password):
        if username in self.account_list:
            return False
        self.account_list[username] = password
        return True

    # check if username and password match
    def login(self, username, password):
        """Returns a bunch of status codes:
        -1: user not found
        0: incorrect password
        1: success
        2: user is already logged in
        """
        if not (username in self.account_list):
            return -1
        chk = self.account_list[username] == password
        if not chk:
            return 0
        elif (self.is_online[username]):
            return 2
        self.is_online[username] = chk
        return 1


    # Moses: will fix below logout/delete account
    def logout(self, username):
        # Assumes that the user is already logged in.
        if not (username in self.account_list):
            return False
        if not (self.is_online[username]): # check if logged in
            return False
        self.is_online[username] = False

    def delete_account(self, username):
        if not (username in self.account_list):
            return False
        del self.account_list[username]
        del self.is_online[username]
        return True

    
# Message Storing mechanisms below
account_store = AccountHandler()

class MessageHandler:
    def __init__(self, store = {}):
        self.message_store = store # username: [message, message, ...]

    def _store_message(self, username, message):
        if not (username in self.message_store):
            self.message_store[username] = []
        self.message_store[username].append(message)
        return True

    def _get_messages(self, username):
        if not (username in self.message_store):
            return []
        return self.message_store[username]

    def _delete_messages(self, username):
        if not (username in self.message_store):
            return False
        del self.message_store[username]
        return True


def handle_user(usersocket, addr):
    print(f"User connected at {addr}")

    connected = True;
    while connected:
        # client will send an encoded message across
        pass
        # msglen = usersocket.recv

def Main():

    # host and port defined in constants

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    print("socket binded to port", PORT)
 
    # put the socket into listening mode
    s.listen(5)
    print("socket is listening")
 
    # a forever loop until client wants to exit
    while True:
 
        # establish connection with client
        c, addr = s.accept()     
        print('Connected to :', addr[0], ':', addr[1])
 
        # Start a new thread and return its identifier
        start_new_thread(threaded, (c,))
    s.close()
 
 
if __name__ == '__main__':
    Main()


