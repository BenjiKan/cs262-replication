# Imports
import socket
import sys
import os
# import mysql.connector
import random

from typing import Optional
 
# import constants from file
from constants import *

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
