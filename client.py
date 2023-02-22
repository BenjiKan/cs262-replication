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

def create_user(s: socket.socket) -> bool:
	"""
	Prompts user for inputs to create a new user
	"""
	# We use this to track interactions with the server
	username = input("Enter username: ")
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
	
	# Handle password input)
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
	retstr = s.recv(1024)
	print(retstr.decode('ascii'))

def att_login(s: socket.socket) -> int:
	"""
	Prompts user for inputs to login to application
	"""
	username = input("Enter username: ")
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
msg_q_lock = threading.Lock()
cross_message_q = deque() # Handles server -> client messages
def recv_handler_thread(s: socket.socket):
	# We make sure that all recv calls are kept to here.
	# Other parts can recv by using the queues
	#print("Thread created")
	while True:
		cur = s.recv(1, socket.MSG_PEEK) # receive status byte
		if not cur:
			continue
		#print("RECEIVED A BYTE: ", cur)
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
			cur = s.recv(2, socket.MSG_PEEK) # check for chunk size
			ln = int.from_bytes(cur[1:], byteorder="little")
			cur = s.recv(2 + ln)
			numchunks = int.from_bytes(cur[2:], byteorder="little")
			print(f"Message from {sender}:", end=" ")
			for i in range(numchunks):
				cur = s.recv(3)
				ln = int.from_bytes(cur[1:3], byteorder='little')
				msg = s.recv(ln).decode('utf-8')
				print(msg, end="")
			print()
			# msg_q.append()
			# msg_q_lock.acquire()
			# msg_q.append(cur)
			# msg_q_lock.release()
		else:
			cur = s.recv(1)
			if cur == CLIENT_LOGGING_OUT:
				return
			elif cur in [CLIENT_MESSAGE_APPROVED, CLIENT_MESSAGE_REJECTED,
						CLIENT_MESSAGE_SENDING_INFO, CLIENT_RETRIEVE_ACCOUNT_LIST,
						CLIENT_ACCOUNT_SENDING]:
				client_q_lock.acquire()
				if cur == CLIENT_MESSAGE_SENDING_INFO:
					ln = int.from_bytes(s.recv(1), byteorder="little")
					cur = s.recv(ln)
				elif cur == CLIENT_RETRIEVE_ACCOUNT_LIST:
					cur = s.recv(CLIENT_ACCOUNT_LIST_NBYTES)
				elif cur == CLIENT_ACCOUNT_SENDING:
					n_cur = s.recv(CLIENT_ACCOUNT_LIST_NBYTES)
					cur = s.recv(int.from_bytes(n_cur, byteorder='little'))
				client_interactions_q.append(cur)
				client_q_lock.release()
			else:
				debugprint("Ill-formed response received from server")

def client_get_response():
	elt = None
	while not elt:
		client_q_lock.acquire()
		if len(client_interactions_q) > 0:
			elt = client_interactions_q.popleft()
		client_q_lock.release()
	return elt

def msg_get_response():
	elt = None
	while not elt:
		msg_q_lock.acquire()
		if len(cross_message_q) > 0:
			elt = cross_message_q.popleft()
		msg_q_lock.release()
	return elt

def send_new_msg(s: socket.socket) -> bool:
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
	full_msg_arr = split_string_length(full_msg)
	arr_len = len(full_msg_arr)
	arr_len_bytelength = (arr_len.bit_length() + 7) // 8 # rounds up, integer division
	arr_len_bytes = arr_len.to_bytes(arr_len_bytelength, byteorder='little')
	s.send(arr_len_bytes) # Sends the length of the chunks.
	ret = client_get_response()
	if ret == CLIENT_MESSAGE_REJECTED:
		retstr = client_get_response()
		print(retstr.decode('ascii'))
		return
	for msg in full_msg_arr:
		msg_utf8 = msg.encode('utf-8')
		msg_len = len(msg_utf8)
		msg_len_bytelength = (msg_len.bit_length() + 7) // 8 # rounds up, integer division
		msg_len_bytes = msg_len.to_bytes(msg_len_bytelength, byteorder='little')
		s.send(msg_len_bytes) # should be safe to not confirm this, as split_string_length caps lengths
		ret = client_get_response()
		s.send(msg_utf8)
		ret = client_get_response()

	# no more handling to do on client end
	return

def delete_account(s: socket.socket) -> bool:
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
	print(retstr.decode('ascii'))
	return ret == CLIENT_MESSAGE_APPROVED

def print_select_users(s: socket.socket, username: str) -> bool: # done
	rstr = input("Enter Python regex (if blank, will select all): ")
	if (len(rstr) > 50): rstr = rstr[:50]
	ln = len(rstr.encode("utf-8")).to_bytes(1, byteorder="little")
	s.send(ln + rstr.encode("utf-8"))
	n_users = client_get_response()
	n_users = int.from_bytes(n_users, byteorder='little')
	user_list = ["All registered users:"]
	for i in range(n_users):
		user_list.append(client_get_response().decode('utf-8'))
		if user_list[-1] == username:
			user_list[-1] += " (you!)"
	print("\n  ".join(user_list))

def Main():
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	s.connect((HOST, PORT))
	status = s.recv(1024)
	debugprint('receive status')
	if status.decode("ascii") == "Connected":
		debugprint("Connection successful")

	logged_in = False
	cur_user = None
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


