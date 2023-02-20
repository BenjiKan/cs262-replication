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
        self.is_online[username] = False
        return True

    # check if username and password match
    def login(self, username: str, password: str) -> int:
        """Returns a bunch of status codes:
        0: success
        1: incorrect password
        2: user is already logged in
        3: user not found
        """
        if not (username in self.account_list):
            return 3
        chk = self.account_list[username] == password
        if not chk:
            return 1
        elif (self.is_online[username]):
            return 2
        self.is_online[username] = chk
        return 0

    # Moses: will fix below logout/delete account
    def logout(self, username) -> bool:
        # Assumes that the user is already logged in.
        if not (username in self.account_list):
            return False
        if not (self.is_online[username]): # check if logged in
            return False
        self.is_online[username] = False
        return True

    def delete_account(self, username):
        # Assumes that the user is logged in.
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


def create_user(c: socket) -> bool:
    usr_len_bytes = c.recv(2)
    print(f"User len bytes: {usr_len_bytes}")
    usr_len = int.from_bytes(usr_len_bytes, byteorder='big')
    print(f"Decoded length: {usr_len}")
    username = c.recv(usr_len).decode('utf-8')
    print(f"Decoded username: {username}")

    pw_len_bytes = c.recv(1)
    print(f"Pw len bytes: {pw_len_bytes}")
    pw_len = int.from_bytes(pw_len_bytes, byteorder='big')
    print(f"Decoded length: {pw_len}")
    password = c.recv(pw_len).decode('utf-8')
    print(f"Decoded password: {password}")

    res = account_store._create_account(username, password)
    c.send(b'1' if res else b'0')
    return res

def att_login(c: socket) -> bool:
    usr_len_bytes = c.recv(2)
    print(f"User len bytes: {usr_len_bytes}")
    usr_len = int.from_bytes(usr_len_bytes, byteorder='big')
    print(f"Decoded length: {usr_len}")
    username = c.recv(usr_len).decode('utf-8')
    print(f"Decoded username: {username}")

    pw_len_bytes = c.recv(1)
    print(f"Pw len bytes: {pw_len_bytes}")
    pw_len = int.from_bytes(pw_len_bytes, byteorder='big')
    print(f"Decoded length: {pw_len}")
    password = c.recv(pw_len).decode('utf-8')
    print(f"Decoded password: {password}")
    
    res = account_store.login(username, password)
    c.send(str(res).encode('ascii'))
    return res == 0 # only 0 is success

def handle_user(usersocket, addr): # thread for user
    print(f"User connected at {addr}")

    # send that the user is connected
    usersocket.send("Connected".encode("ascii"))
    logged_in = False
    while True: # pre-login
        mode = usersocket.recv(1)
        if not mode:
            print(f"Closing connection at {addr}")
            break
        if mode.decode('ascii') == "1":
            create_user(usersocket)
            print("All users:")
            print(account_store.account_list)
        elif mode.decode('ascii') == "2":
            att_login(usersocket)
            pass
        else: # option 3. Exit
            print(f"Closing connection at {addr}")
            break

    while logged_in: # if logged in, do stuff
        pass

    usersocket.close()
    return
    while logged_in:
        pass

    usersocket.close()

def Main():
    # host and port defined in constants

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    print("socket binded to port", PORT)
 
    # put the socket into listening mode
    s.listen(5)
    print("socket is listening")
 
    # a forever loop until client wants to exit
    try:
        while True:
    
            # establish connection with client
            c, addr = s.accept()     
            print('Connected to :', addr[0], ':', addr[1])
    
            # Start a new thread and return its identifier
            start_new_thread(handle_user, (c,addr))
    except KeyboardInterrupt:
        s.close()
        return
    except Exception as e:
        print(e)
        s.close()
        return
    s.close()

def bankMain():

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


