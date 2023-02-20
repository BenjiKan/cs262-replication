##Ref: https://www.geeksforgeeks.org/socket-programming-multi-threading-python/
# Imports
import socket
import sys
import os

# import constants

from constants import *

def create_user(s: socket) -> bool:
	username = input("Enter username:")
	while len(username) > 280:
		username = input("Username must be at most 280 characters.\nEnter username:")
	usrn_utf8 = username.encode('utf-8')
	usrn_len = len(usrn_utf8)
	usrn_len_bytes = usrn_len.to_bytes(2, byteorder='big')
	s.send(usrn_len_bytes)
	s.send(usrn_utf8)

	password, cnfm_pw = "", None
	while password != cnfm_pw:
		if cnfm_pw:
			print("Passwords do not match.")
		password = input("Enter password:")
		while len(password) > 24 or len(password) < 6:
			password = input("Password must be 6-24 characters long.\nEnter password:")
		cnfm_pw = input("Confirm password:")

	pw_utf8 = password.encode('utf-8')
	pw_len = len(pw_utf8)
	pw_len_bytes = pw_len.to_bytes(1, byteorder='big')
	s.send(pw_len_bytes)
	s.send(pw_utf8)

	res = s.recv(1).decode('ascii')
	return res == "1"

def att_login(s: socket) -> int:
	username = input("Enter username:")
	while len(username) > 280:
		username = input("Username must be at most 280 characters.\nEnter username:")
	password = input("Enter password:")
	if len(password) > 60:
		# in create user, we made this 6-24 characters
		# so this is fine
		password = password[:60]

	# Same encoding as in create_user
	usrn_utf8 = username.encode('utf-8')
	usrn_len = len(usrn_utf8)
	usrn_len_bytes = usrn_len.to_bytes(2, byteorder='big')
	pw_utf8 = password.encode('utf-8')
	pw_len = len(pw_utf8)
	pw_len_bytes = pw_len.to_bytes(1, byteorder='big')
	pw_ascii = password.encode('ascii')
	pw_len = len(password)

	s.send(usrn_len_bytes)
	s.send(usrn_utf8)
	s.send(pw_len_bytes)
	s.send(pw_utf8)

	res = s.recv(1).decode('ascii')
	return int(res)

def Main():
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	s.connect((HOST, PORT))
	status = s.recv(1024)
	print('receive status')
	if status.decode("ascii") == "Connected":
		print("Connection successful")

	logged_in = False
	while not logged_in:
		print("Options:\n1. Create account\n2. Login\n3. Exit")
		choice = ""
		while choice not in ["1", "2", "3"]:
			if choice != "":
				print("Please select a valid option.")
			choice = input("Select choice:")
		s.send(choice.encode('ascii'))
		if choice == "1":
			if create_user(s):
				print("User successfully created")
			else:
				print("User already exists")
		elif choice == "2":
			res = att_login(s)
			if res == 0:
				print("Login successful.")
				logged_in = True
			elif res == 1:
				print("Incorrect password.")
			elif res == 2:
				print("User is currently logged in on another client.")
			else: #res == 3
				print("User does not exist.")
		else:
			s.close()
			return
		print()
		
	while logged_in:
		pass
	
	# s.send()

	try:
		while True:
			pass
	except KeyboardInterrupt:
		pass
	s.close()

def bankMain():
	# host and port defined in constants

	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	# connect to server on local computer
	s.connect((HOST, PORT))

	# message you send to server
	#message = "V for vendetta"
	while True:
		# message sent to server
		# message received from server
		# ask the client whether he wants to continue
		ans = input('\nEnter your request:')
		if ans == '':
			ans2 = input('\nDo you want to continue(y/n) :')
			if ans2 =='y':
				continue
			else:
				break
		else:
			s.send(ans.encode('ascii'))
			data = s.recv(1024)
			# print the received message
			# here it would be a reverse of sent message
			print('Received from the server :',str(data.decode('ascii')))
			continue
	# close the connection
	s.close()

if __name__ == '__main__':
	Main()


