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

# connect to CENTRAL HANDLER (wait for acknowledgement), send username and password from log in

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


