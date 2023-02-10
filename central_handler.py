# Imports
import socket
import sys
import os

from constants import *

SERVER = socket.gethostname()
# Address is hence (SERVER, PORT)

# Create socket object, use AF_INET and SOCKSTREAM
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((SERVER, PORT))
serversocket.listen(10) # for testing purposes

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

while True:
    (clientsocket,  addr) = serversocket.accept()