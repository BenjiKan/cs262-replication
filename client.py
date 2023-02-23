##Ref: https://www.geeksforgeeks.org/socket-programming-multi-threading-python/
# Imports
import socket
import sys
import os

from _thread import *
import threading

# import constants
from constants import *

from typing import List
from collections import deque

debugprint = print
debugprint = lambda *args: None
# uncomment the line above when not debugging

# Helper function to take a message and split it off into smaller strings
# MAX_MSG_LENGTH is defined in constants.py
def split_string_length(s: str, l: int = MAX_MSG_LENGTH) -> List[str]:
	"""
	Splits s into an array of strings each of length at most l.
	"""
	ret = []
	sz = len(s)
	cur = 0
	while cur < sz:
		nx = min(sz, cur + l)
		ret.append(s[cur:nx])
		cur = nx
	return ret

# Client wants to create a new user
# s: server socket
def create_user(s: socket.socket) -> bool:
	"""
	Prompts user for inputs to create a new user
	"""
	# We use this to track interactions with the server
	username = input("Enter username: ")
	# Send length first before sending string. We use this approach whenever
	# sending strings to ensure that no excess bytes are sent
	usrn_utf8 = username.encode('utf-8')
	usrn_len = len(usrn_utf8)
	usrn_len_bytelength = (usrn_len.bit_length() + 7) // 8 # rounds up, integer division
	usrn_len_bytes = usrn_len.to_bytes(usrn_len_bytelength, byteorder='little')
	s.send(usrn_len_bytes)
	ret = s.recv(1) # expect confirmation byte from server
	if ret == CLIENT_MESSAGE_REJECTED:
		# Failure in username
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return
	s.send(usrn_utf8)
	ret = s.recv(1)
	
	# Handle password input
	password = input("Enter password: ")
	cnfm_pw = input("Confirm password: ")
	pw_utf8 = password.encode('utf-8')
	pw_len = len(pw_utf8)
	pw_len_bytelength = (pw_len.bit_length() + 7) // 8
	pw_len_bytes = pw_len.to_bytes(pw_len_bytelength, byteorder='little')
	s.send(pw_len_bytes)		
	ret = s.recv(1)
	if ret == CLIENT_MESSAGE_REJECTED:
		# Failure in password
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return
	s.send(pw_utf8)
	ret = s.recv(1)

	# Handle password confirmation
	cnfm_pw_utf8 = cnfm_pw.encode('utf-8')
	cnfm_pw_len = len(cnfm_pw_utf8)
	cnfm_pw_len_bytelength = (cnfm_pw_len.bit_length() + 7) // 8
	cnfm_pw_len_bytes = cnfm_pw_len.to_bytes(cnfm_pw_len_bytelength, byteorder='little')
	s.send(cnfm_pw_len_bytes)		
	ret = s.recv(1)
	if ret == CLIENT_MESSAGE_REJECTED:
		# Failure in confirm password
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return

	s.send(cnfm_pw_utf8)

	# Final message from server
	ret = s.recv(1) # final status, CLIENT_MESSAGE_APPROVED/CLIENT_MESSAGE_REJECTED
	retstr = s.recv(1024) # status message
	print(retstr.decode('ascii'))

def att_login(s: socket.socket) -> int:
	"""
	Prompts user for inputs to login to application
	"""
	username = input("Enter username: ")
	# same approach to send strings -- encode, send size, then send actual string
	# while waiting for confirmation at each step
	usrn_utf8 = username.encode('utf-8')
	usrn_len = len(usrn_utf8)
	usrn_len_bytelength = (usrn_len.bit_length() + 7) // 8 # rounds up, integer division
	usrn_len_bytes = usrn_len.to_bytes(usrn_len_bytelength, byteorder='little')
	s.send(usrn_len_bytes)
	ret = s.recv(1) # expect 1 bit from server
	if ret == CLIENT_MESSAGE_REJECTED:
		# Failure in username
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return
	s.send(usrn_utf8)
	ret = s.recv(1)
	
	password = input("Enter password: ")
	pw_utf8 = password.encode('utf-8')
	pw_len = len(pw_utf8)
	pw_len_bytelength = (pw_len.bit_length() + 7) // 8
	pw_len_bytes = pw_len.to_bytes(pw_len_bytelength, byteorder='little')
	s.send(pw_len_bytes)		
	ret = s.recv(1)
	if ret == CLIENT_MESSAGE_REJECTED:
		# Failure in password
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return
	s.send(pw_utf8)
	ret = s.recv(1)

	# Check return status
	res = s.recv(1).decode('ascii') #Server message is not very long -- see server code
	ln = int.from_bytes(s.recv(1), byteorder="little")
	resmsg = s.recv(ln)
	print(resmsg.decode('ascii'))
	return int(res), username

# Section: Response queue
msg_q = deque() #
client_q_lock = threading.Lock()
client_interactions_q = deque() # Handles messages client -> server confirm
cross_message_q = deque() # Handles server -> client messages
def recv_handler_thread(s: socket.socket):
	"""
	Handles all recv calls to the socket
	"""
	# We make sure that all recv calls are kept to here.
	# Other parts can recv by using the queues
	#print("Thread created")
	while True:
		# receive status byte using peek to keep it in the buffer
		cur = s.recv(1, socket.MSG_PEEK)
		if not cur:
			continue
		if cur in [SERVER_SENDING_MESSAGE]:
			# Handles messages that come directly without client requests
			# e.g. receiving a message from another user
			debugprint("Acquiring messages")
			cur = s.recv(2, socket.MSG_PEEK)
			debugprint(cur, cur[1:])
			ln = int.from_bytes(cur[1:], byteorder="little")
			debugprint(cur)
			cur = s.recv(2 + ln)
			sender = cur[2:].decode('utf-8')
			cur = s.recv(2, socket.MSG_PEEK) # check for chunk byte size
			ln = int.from_bytes(cur[1:], byteorder="little")
			cur = s.recv(2 + ln)
			numchunks = int.from_bytes(cur[2:], byteorder="little")
			print(f"Message from {sender}:", end=" ")
			for i in range(numchunks):
				cur = s.recv(3) #confirmation byte + message chunk size (< 256*2-1)
				ln = int.from_bytes(cur[1:3], byteorder='little')
				msg = s.recv(ln).decode('utf-8')
				print(msg, end="")
			print()
		else: # server interaction
			cur = s.recv(1)
			if cur == CLIENT_LOGGING_OUT:
				# When logging out, server sends a specific byte. This tells
				# the function to return so that the thread closes
				return
			elif cur in [CLIENT_MESSAGE_APPROVED, CLIENT_MESSAGE_REJECTED,
						CLIENT_MESSAGE_SENDING_INFO, CLIENT_RETRIEVE_ACCOUNT_LIST,
						CLIENT_ACCOUNT_SENDING]:
				# Bye race conditions -- locks are great
				client_q_lock.acquire()
				# CLIENT_MESSAGE_SENDING_INFO indicates that a message is to be sent
				if cur == CLIENT_MESSAGE_SENDING_INFO:
					ln = int.from_bytes(s.recv(1), byteorder="little")
					cur = s.recv(ln)
				# CLIENT_RETRIEVE_ACCOUNT_LIST indicates account list is being sent
				elif cur == CLIENT_RETRIEVE_ACCOUNT_LIST:
					cur = s.recv(CLIENT_ACCOUNT_LIST_NBYTES)
				# CLIENT_ACCOUNT_SENDING indicates account name being sent
				elif cur == CLIENT_ACCOUNT_SENDING:
					n_cur = s.recv(CLIENT_ACCOUNT_LIST_NBYTES)
					cur = s.recv(int.from_bytes(n_cur, byteorder='little'))
				client_interactions_q.append(cur) # push in the important stuff
				client_q_lock.release()
			else:
				debugprint("Ill-formed response received from server")

# Basically, this replaces most client calls to .recv for concurrency purposes
# client_interaction_q will store the pending messages from the server, and we
# simply unlock/lock each time and check. Avoiding bad race conditions!
def client_get_response():
	"""
	Blocks until a response is received from the server
	"""
	elt = None
	while not elt:
		client_q_lock.acquire()
		if len(client_interactions_q) > 0:
			elt = client_interactions_q.popleft()
		client_q_lock.release()
	return elt

def send_new_msg(s: socket.socket) -> bool:
	"""
	Sends a new message to a user
	"""
	# Ensures that it is a valid recipient before user can input the message
	recipient = input("Enter user: ")
	rec_utf8 = recipient.encode('utf-8')
	rec_len = len(rec_utf8)
	rec_len_bytelength = (rec_len.bit_length() + 7) // 8 # rounds up, integer division
	rec_len_bytes = rec_len.to_bytes(rec_len_bytelength, byteorder='little')
	debugprint("Sending bytes", rec_len_bytes)
	s.send(rec_len_bytes)
	debugprint("sent")
	ret = client_get_response() # expect 1 bit from server
	if ret == CLIENT_MESSAGE_REJECTED:
		retstr = client_get_response()
		print(retstr.decode('ascii'))
		return
	s.send(rec_utf8) # sends recipient name
	ret = client_get_response()
	if ret == CLIENT_MESSAGE_REJECTED:
		retstr = client_get_response()
		print(retstr.decode('ascii'))
		return

	# Recipient confirmed, now sending message itself
	full_msg = input("Enter message:")
	full_msg_arr = split_string_length(full_msg) # split into smaller chunks
	arr_len = len(full_msg_arr)
	arr_len_bytelength = (arr_len.bit_length() + 7) // 8 # rounds up, integer division
	arr_len_bytes = arr_len.to_bytes(arr_len_bytelength, byteorder='little')
	s.send(arr_len_bytes) # Sends the length of the chunks.
	ret = client_get_response()
	if ret == CLIENT_MESSAGE_REJECTED:
		retstr = client_get_response() # get error message
		print(retstr.decode('ascii'))
		return
	for msg in full_msg_arr:
		msg_utf8 = msg.encode('utf-8')
		msg_len = len(msg_utf8)
		msg_len_bytelength = (msg_len.bit_length() + 7) // 8 # rounds up, integer division
		msg_len_bytes = msg_len.to_bytes(msg_len_bytelength, byteorder='little')
		s.send(msg_len_bytes) # should be safe to not confirm this, as split_string_length caps lengths
		ret = client_get_response() # absorbs the confirmation messages sent
		s.send(msg_utf8)
		ret = client_get_response()

	# no more handling to do on client end
	return

def delete_account(s: socket.socket) -> bool:
	"""
	Deletes the account
	"""
	# We make the user confirm that they want to delete the account
	print("Are you sure you want to delete your account?")
	username = input("Enter username to confirm: ")
	usrn_utf8 = username.encode('utf-8')
	usrn_len = len(usrn_utf8)
	usrn_len_bytelength = (usrn_len.bit_length() + 7) // 8 # rounds up, integer division
	usrn_len_bytes = usrn_len.to_bytes(usrn_len_bytelength, byteorder='little')
	s.send(usrn_len_bytes)
	ret = client_get_response()
	if ret == CLIENT_MESSAGE_REJECTED:
		# invalid input
		retstr = client_get_response()
		print(retstr.decode('ascii'))
		return
	s.send(usrn_utf8)
	ret = client_get_response()
	retstr = client_get_response()
	print(retstr.decode('ascii')) # prints message from server
	return ret == CLIENT_MESSAGE_APPROVED

def print_select_users(s: socket.socket, username: str) -> bool: 
	"""
	Prints a list of users that match a regex
	"""
	rstr = input("Enter Python regex (if blank, will select all): ")
	# Cap the length of the regex. Realistically, it shouldn't be too too long
	if (len(rstr) > 50): rstr = rstr[:50]
	ln = len(rstr.encode("utf-8")).to_bytes(1, byteorder="little")
	s.send(ln + rstr.encode("utf-8"))
	n_users = client_get_response()
	n_users = int.from_bytes(n_users, byteorder='little')
	user_list = ["All registered users:"]
	for i in range(n_users):
		user_list.append(client_get_response().decode('utf-8'))
		if user_list[-1] == username:
			user_list[-1] += " (you!)" # Indicates the user if they are on the list
	print("\n  ".join(user_list))

def Main():
	"""
	Main function, to be called when the program is run
	"""
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	s.connect((HOST, PORT))
	status = s.recv(1024)
	debugprint('receive status')
	if status.decode("ascii") == "Connected":
		debugprint("Connection successful")

	logged_in = False
	cur_user = None
	# This repl just alternates between handling pre-login and post-login stuff
	while not logged_in:
		print("Options:\n1. Create account\n2. Login\n3. Exit")
		choice = ""
		while choice not in ["1", "2", "3"]:
			if choice != "":
				print("Please select a valid option.")
			choice = input("Select choice:")
		s.send(choice.encode('ascii'))
		if choice == "1":
			create_user(s)
		elif choice == "2":
			res, cur_user = att_login(s)
			if res == 0:
				logged_in = True
		else: # choice == "3"
			ans = input("Are you sure you want to exit? (enter 'y' to confirm) ")
			if (ans != 'y'):
				continue
			s.close()
			return
		print()

		# If the user is logged in then we do the stuff below, otherwise go
		# to the end and repeat the above pre-login stuff

		# Make thread for message listener
		if logged_in:
			start_new_thread(recv_handler_thread, (s,))
			while logged_in:
				print(f"Logged in as {cur_user}")
				print("Options:\n1. Send message\n2. Delete account\n3. List all users\n4. Logout")
				choice = ""
				while choice not in ["1", "2", "3", "4"]:
					if choice != "":
						print("Please select a valid option.")
					choice = input("Select choice:")
				if choice == '1':
					s.send(choice.encode('ascii'))
					send_new_msg(s)
				elif choice == '2':
					s.send(choice.encode('ascii'))
					if delete_account(s):
						# using recv in server code to block and separate
						# message from CLIENT_LOGGING_OUT byte
						s.send(CLIENT_MESSAGE_APPROVED)
						logged_in = False
				elif choice == '3': 
					s.send(choice.encode('ascii'))
					print_select_users(s, cur_user)
				else: # choice == '4'
					ans = input("Are you sure you want to logout? (enter 'y' to confirm) ")
					if (ans != 'y'):
						continue
					s.send(choice.encode('ascii'))
					logged_in, cur_user = False, None
					print("Logging out...")
				print()

	try:
		while True:
			pass
	except KeyboardInterrupt:
		pass
	s.close()

if __name__ == '__main__':
	Main()