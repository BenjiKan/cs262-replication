#Ref: https://www.geeksforgeeks.org/socket-programming-multi-threading-python/

# Imports
import socket
import sys
import os
# import mysql.connector
import random

from typing import Optional
 
# import thread module
from _thread import *
import threading

accountName_table={}
accountBalance_table={}

p_lock = threading.Lock()

# import constants
from constants import *



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
        self.sock = {usr: None for usr in self.account_list.keys()}
    
    def _create_account(self, username, password):
        if username in self.account_list:
            return False
        self.account_list[username] = password
        self.is_online[username] = False
        self.sock[username] = None
        return True

    def user_exists(self, username):
        return username in self.account_list
    
    def is_online(self, username):
        if not self.user_exists(username): return False
        return self.is_online[username]

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

    def update_sock(self, username: str, c: Optional[socket.socket]):
        self.sock[username] = c

    # Moses: will fix below logout/delete account
    def logout(self, username) -> bool:
        # Assumes that the user is already logged in.
        if not (username in self.account_list):
            return False
        if not (self.is_online[username]): # check if logged in
            return False
        self.is_online[username] = False
        self.update_sock(username, None)
        return True

    def delete_account(self, username):
        """
        Attempts to delete account identified by username
        @username: username to delete
        Returns True if deletion is successful
        """
        # Assumes that the user is logged in.
        if not (username in self.account_list):
            return False
        del self.account_list[username]
        del self.is_online[username]
        del self.sock[username]
        return True

    
# Message Storing mechanisms below
account_store = AccountHandler()

class Message:
    def __init__(self, sender, content, id, prv):
        self.sender = sender
        self.content = content
        self.id = id 
        self.prv = prv

class MessageHandler:
    def __init__(self, store = {}):
        self.message_store = store # username: [message, message, ...]
        self.message_count = 0

    def _store_message(self, username, message: Message):
        prv = -1;
        if not (username in self.message_store):
            self.message_store[username] = []
        else:
            prv = self.message_store[username][-1].id
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

    def push_new_message(self, recipient, sender, body):
        p_lock.acquire()
        self._store_message(recipient,
                            Message(sender, body, self.message_count, -1))
        self.message_count += 1
        p_lock.release()

message_handler = MessageHandler()

def create_user(c: socket.socket) -> bool:
    usr_len_bytes = c.recv(1024)
    usr_len = -1
    client_send_msg = CLIENT_MESSAGE_APPROVED
    if len(usr_len_bytes) > 1: # username is definitely too long, > 256
        client_send_msg = CLIENT_MESSAGE_REJECTED
    else:
        usr_len = int.from_bytes(usr_len_bytes, byteorder='little')
        if usr_len > 50:
            client_send_msg = CLIENT_MESSAGE_REJECTED
            usr_len = -1
    c.send(client_send_msg)
    if usr_len < 0:
        msg = "Username is too long"
        print(msg)
        c.send(msg.encode('ascii'))
        return False
    usr_utf8 = c.recv(usr_len)
    username = usr_utf8.decode('utf-8')
    c.send(CLIENT_MESSAGE_APPROVED) # send username received

    pw_len_bytes = c.recv(1024)
    pw_len = -1
    client_send_msg = CLIENT_MESSAGE_APPROVED
    if len(pw_len_bytes) > 1: # password > 256 characters
        client_send_msg = CLIENT_MESSAGE_REJECTED
    else:
        pw_len = int.from_bytes(pw_len_bytes, byteorder='little')
        if pw_len > 24 or pw_len < 6:
            client_send_msg = CLIENT_MESSAGE_REJECTED
            pw_len = -1
    c.send(client_send_msg)
    if pw_len < 0:
        msg = "Password must be between 6 and 24 characters"
        print(msg)
        c.send(msg.encode('ascii'))
        return False;
    pw_utf8 = c.recv(pw_len)
    password = pw_utf8.decode('utf-8')
    c.send(CLIENT_MESSAGE_APPROVED) # send pw received

    cnfm_pw_len_bytes = c.recv(1024)
    cnfm_pw_len = -1
    client_send_msg = CLIENT_MESSAGE_APPROVED
    if len(cnfm_pw_len_bytes) > 1: # password > 256 characters
        client_send_msg = CLIENT_MESSAGE_REJECTED
    else:
        cnfm_pw_len = int.from_bytes(cnfm_pw_len_bytes, byteorder='little')
        if cnfm_pw_len > 24 or cnfm_pw_len < 6:
            client_send_msg = CLIENT_MESSAGE_REJECTED
            cnfm_pw_len = -1
    c.send(client_send_msg)
    if cnfm_pw_len < 0:
        msg = "Password must be between 6 and 24 characters"
        print(msg)
        c.send(msg.encode('ascii'))
        return False;
    cnfm_pw_utf8 = c.recv(cnfm_pw_len)
    cnfmpw = cnfm_pw_utf8.decode('utf-8')
    print(f"Decoded confirm: {cnfmpw}")
    
    res = False
    if password != cnfmpw:
        msg = "Passwords do not match"
    else:
        res = account_store._create_account(username, password)
        if res:
            msg = "User successfully created"
        else:
            msg = "User already exists"
    c.send(CLIENT_MESSAGE_APPROVED if res else CLIENT_MESSAGE_REJECTED)
    c.send(msg.encode("ascii"))
    return res

def att_login(c: socket.socket) -> bool:
    usr_len_bytes = c.recv(1024)
    usr_len = -1
    client_send_msg = CLIENT_MESSAGE_APPROVED
    if len(usr_len_bytes) > 1: # username is definitely too long, > 256
        client_send_msg = CLIENT_MESSAGE_REJECTED
    else:
        usr_len = int.from_bytes(usr_len_bytes, byteorder='little')
        if usr_len > 50:
            client_send_msg = CLIENT_MESSAGE_REJECTED
            usr_len = -1
    c.send(client_send_msg)
    if usr_len < 0:
        msg = "Username is too long"
        print(msg)
        c.send(msg.encode('ascii'))
        return False
    usr_utf8 = c.recv(usr_len)
    username = usr_utf8.decode('utf-8')
    c.send(CLIENT_MESSAGE_APPROVED) # send username received

    pw_len_bytes = c.recv(1024)
    pw_len = -1
    client_send_msg = CLIENT_MESSAGE_APPROVED
    if len(pw_len_bytes) > 1: # password > 256 characters
        client_send_msg = CLIENT_MESSAGE_REJECTED
    else:
        pw_len = int.from_bytes(pw_len_bytes, byteorder='little')
        if pw_len > 100:
            # potentially malicious input. We specified in user creation that
            # passwords were 6-24 characters
            client_send_msg = CLIENT_MESSAGE_REJECTED
            pw_len = -1
    c.send(client_send_msg)
    if pw_len < 0:
        msg = "Password incorrect"
        print(msg)
        c.send(msg.encode('ascii'))
        return False;
    pw_utf8 = c.recv(pw_len)
    password = pw_utf8.decode('utf-8')
    c.send(CLIENT_MESSAGE_APPROVED) # send pw received
    
    res = account_store.login(username, password)
    if res == 0:
        msg = "Login successful."
        account_store.update_sock(username, c)
    elif res == 1:
        msg = "Incorrect password."
    elif res == 2:
        msg = "User is currently logged in on another client."
    else: #res == 3
        msg = "User does not exist."
    c.send(str(res).encode('ascii'))
    c.send(msg.encode('ascii'))
    return (res == 0), username

def attempt_deliver_messages(sender):pass

def user_send_msg(c: socket.socket, sender: str) -> bool:
    print("Start receive message")
    usr_len_bytes = c.recv(1024)
    usr_len = -1
    client_send_msg = CLIENT_MESSAGE_APPROVED
    if len(usr_len_bytes) > 1:
        client_send_msg = CLIENT_MESSAGE_REJECTED
    else:
        usr_len = int.from_bytes(usr_len_bytes, byteorder='little')
        if usr_len > 50:
            client_send_msg = CLIENT_MESSAGE_REJECTED
            usr_len = -1
    c.send(client_send_msg)
    if usr_len < 0: # Rejected case
        c.send(CLIENT_MESSAGE_SENDING_INFO)
        msg = "User not found"
        c.send(msg.encode('ascii'))
        return False
    usr_utf8 = c.recv(usr_len)
    recipient = usr_utf8.decode('utf-8')
    if not account_store.user_exists(recipient):
        c.send(CLIENT_MESSAGE_REJECTED)
        c.send(CLIENT_MESSAGE_SENDING_INFO)
        msg = "Recipient does not exist"
        c.send(msg.encode('ascii'))
        return
    else:
        c.send(CLIENT_MESSAGE_APPROVED)
    # Handling recipient done, now handle receive messages
    num_chunk_bytes = c.recv(1024)
    num_chunks = int.from_bytes(num_chunk_bytes, byteorder="little")
    if num_chunks > MAX_MSG_CHUNK or num_chunks <= 0:
        # Next two lines emptys the socket send queue, in case client sends a ton of data
        tmp = c.recv(1024)
        while tmp: tmp = c.recv(1024)
        c.send(CLIENT_MESSAGE_REJECTED)
        c.send(CLIENT_MESSAGE_SENDING_INFO)
        msg = "Message is too long to send"
        c.send(msg.encode('ascii'))
        return
    else:
        c.send(CLIENT_MESSAGE_APPROVED)
    complete_msg = [num_chunk_bytes]
    for i in range(num_chunks):
        msg_len_bytes = c.recv(1024)
        c.send(CLIENT_MESSAGE_APPROVED)
        msg_len = int.from_bytes(msg_len_bytes, byteorder="little")
        msg_utf8 = c.recv(msg_len).decode('utf-8')
        complete_msg.append(msg_utf8)
        c.send(CLIENT_MESSAGE_APPROVED)
    message_handler.push_new_message(recipient, sender, complete_msg)
    print(f"Have {message_handler.message_count} messages")
    print(message_handler.message_store)
    

def list_all_users(c: socket.socket):
    pass
def att_delete_account(c: socket.socket, username: str) -> bool:
    usr_len_bytes = c.recv(1024)
    usr_len = -1
    if not usr_len_bytes:
        pass
    elif len(usr_len_bytes) <= 1: #Within allowable range
        usr_len = int.from_bytes(usr_len_bytes, byteorder='little')
        if usr_len > 50:
            usr_len = -1
    if usr_len < 0: # Rejected case
        c.send(CLIENT_MESSAGE_REJECTED)
        c.send(CLIENT_MESSAGE_SENDING_INFO)
        msg = "Confirmation failed - invalid input"
        c.send(msg.encode('ascii'))
        return False
    # Passes initial check, get username
    c.send(CLIENT_MESSAGE_APPROVED)
    usr_utf8 = c.recv(usr_len)
    cmp_usr = usr_utf8.decode('utf-8')
    if cmp_usr != username or (not account_store.delete_account(username)):
        c.send(CLIENT_MESSAGE_REJECTED)
        c.send(CLIENT_MESSAGE_SENDING_INFO)
        msg = "Confirmation failed -- invalid username"
        c.send(msg.encode('ascii'))
        return False
    c.send(CLIENT_MESSAGE_APPROVED)
    c.send(CLIENT_MESSAGE_SENDING_INFO)
    msg = "Confirmed -- user successfully deleted"
    c.send(msg.encode('ascii'))
    return True
    
def handle_user(c, addr): # thread for user
    print(f"User connected at {addr}")

    # send that the user is connected
    c.send("Connected".encode("ascii"))
    logged_in = False
    cur_user = None
    while not logged_in: # pre-login
        mode = c.recv(1)
        if not mode:
            print(f"Closing connection at {addr}")
            break
        if mode.decode('ascii') == "1":
            create_user(c)
            print("All users:")
            print(account_store.account_list)
        elif mode.decode('ascii') == "2":
            logged_in, cur_user = att_login(c)
        else: # option 3. Exit
            print(f"Closing connection at {addr}")
            break
    
        # Only do the below if logged in, otherwise skip and
        # repeat user login procedures
        if (logged_in):
            print(f"User from {addr} logged in as {cur_user}")

        while logged_in: # if logged in, do stuff
            mode = c.recv(1)
            if not mode:
                print(f"Closing connection at {addr}")
                break
            mode = mode.decode('ascii')
            print(f"User at {addr}: {mode}")
            if mode == "1":
                user_send_msg(c, cur_user)
            elif mode == "2":
                if (att_delete_account(c, cur_user)):
                    mode = c.recv(1) # used for blocking purposes
                    c.send(CLIENT_LOGGING_OUT)
                    logged_in = False
                    cur_user = None
                print("All users:")
                print(account_store.account_list)
            else:
                c.send(CLIENT_LOGGING_OUT)
                account_store.logout(cur_user)
                print(f"User at {addr} logged out from {cur_user}")
                logged_in = False
                cur_user = None
                break

    c.close()
    return

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


