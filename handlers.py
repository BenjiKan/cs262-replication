# Imports
import socket
import sys
import os
# import mysql.connector
import random

from typing import Optional, List, Tuple
 
# import thread module
from _thread import *
import threading

# import constants from file
from constants import *

class AccountHandler:
    """
    Handles account creation, login, and logout.
    """
    def __init__(self, store = {}):
        """
        Initializes the account handler with the given store.
        """
        self.account_list = store # username: password
        # username: currently online or not
        self.is_online = {usr: False for usr in self.account_list.keys()}
        self.sock = {usr: None for usr in self.account_list.keys()}
    
    def _create_account(self, username, password):
        """
        Creates an account with the given username and password.
        Returns True if account creation is successful
        """
        if username in self.account_list:
            return False
        self.account_list[username] = password
        self.is_online[username] = False
        self.sock[username] = None
        return True

    def user_exists(self, username):
        """
        Checks if username exists
        """
        return username in self.account_list
    
    def is_online(self, username):
        """
        Checks if username is online
        """
        if not self.user_exists(username): return False
        return self.is_online[username]

    # check if username and password match
    def login(self, username: str, password: str) -> int:
        """
        Logs in the user with the given username and password.
        Returns a bunch of status codes:
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
        """
        Updates the socket of the user with the given username.
        """
        self.sock[username] = c

    def logout(self, username) -> bool:
        """
        Logs out the user with the given username.
        Returns True if logout is successful
        """
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

p_lock = threading.Lock()

class Message:
    """
    Message class
    """
    def __init__(self, sender: str, content: List[str], id, prv):
        self.sender = sender
        self.content = content
        self.id = id 
        self.prv = prv


class MessageHandler:
    """
    Handles message sending and receiving.
    """
    def __init__(self, store = {}):
        """
        Initializes the message handler with the given store.
        """
        self.message_store = store # username: [message, message, ...]
        self.message_count = 0
        self.last_idx = {usr: -1 for usr in store}

    def init_user(self, username):
        """
        Initializes a user if they do not exist
        """
        if not (username in self.message_store):
            self.message_store[username] = []
            self.last_idx[username] = -1
            return True
        return False

    def _store_message(self, username, message: Message):
        """
        Stores a message in the message store.
        """
        prv = -1;
        if not self.init_user(username) and len(self.message_store[username]) > 0:
            prv = self.message_store[username][-1].id
        message.prv = prv
        self.message_store[username].append(message)
        return True

    def _get_messages(self, username):
        """
        Gets all messages for a user.
        """
        if not (username in self.message_store):
            return []
        return self.message_store[username]

    def _delete_messages(self, username):
        """
        Deletes all messages for a user.
        """
        if not (username in self.message_store):
            return False
        del self.message_store[username]
        return True

    def push_new_message(self, recipient: str, sender: str, body: List[str]):
        """
        Pushes a new message to the message store.
        """
        p_lock.acquire()
        self._store_message(recipient,
                            Message(sender, body, self.message_count, -1))
        self.message_count += 1
        p_lock.release()

    def fetch_messages(self, recipient: str) -> Tuple[List[Message], int]:
        """
        Fetches all messages for a user.
        """
        p_lock.acquire()
        self.init_user(recipient)
        cur_idx = self.last_idx[recipient]
        n = len(self.message_store[recipient])
        ret = []
        while cur_idx + 1 < n:
            cur_idx += 1
            ret.append(self.message_store[recipient][cur_idx])
        p_lock.release()
        return ret, cur_idx
