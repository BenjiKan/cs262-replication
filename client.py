##Ref: https://www.geeksforgeeks.org/socket-programming-multi-threading-python/
# Imports
import socket
import sys
import os

# import constants

from constants import *

def create_user(s: socket) -> bool:
	# We use this to track interactions with the server
	username = input("Enter username: ")
	usrn_utf8 = username.encode('utf-8')
	usrn_len = len(usrn_utf8)
	usrn_len_bytelength = (usrn_len.bit_length() + 7) // 8 # rounds up, integer division
	usrn_len_bytes = usrn_len.to_bytes(usrn_len_bytelength, byteorder='little')
	s.send(usrn_len_bytes)
	ret = s.recv(1) # expect 1 bit from server
	if ret.decode('ascii') == '0':
		# Failure in username
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return
	s.send(usrn_utf8)
	ret = s.recv(1)
	
	password = input("Enter password: ")
	cnfm_pw = input("Confirm password: ")
	pw_utf8 = password.encode('utf-8')
	pw_len = len(pw_utf8)
	pw_len_bytelength = (pw_len.bit_length() + 7) // 8
	pw_len_bytes = pw_len.to_bytes(pw_len_bytelength, byteorder='little')
	s.send(pw_len_bytes)		
	ret = s.recv(1)
	if ret.decode('ascii') == '0':
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
	if ret.decode('ascii') == '0':
		# Failure in confirm password
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return

	s.send(cnfm_pw_utf8)

	# Final message from server
	ret = s.recv(1) # final status, b'1' or b'0'
	retstr = s.recv(1024)
	print(retstr.decode('ascii'))

def att_login(s: socket) -> int:
	username = input("Enter username: ")
	usrn_utf8 = username.encode('utf-8')
	usrn_len = len(usrn_utf8)
	usrn_len_bytelength = (usrn_len.bit_length() + 7) // 8 # rounds up, integer division
	usrn_len_bytes = usrn_len.to_bytes(usrn_len_bytelength, byteorder='little')
	s.send(usrn_len_bytes)
	ret = s.recv(1) # expect 1 bit from server
	if ret.decode('ascii') == '0':
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
	if ret.decode('ascii') == '0':
		# Failure in password
		retstr = s.recv(1024)
		print(retstr.decode('ascii'))
		return
	s.send(pw_utf8)
	ret = s.recv(1)

	# Check return status
	res = s.recv(1).decode('ascii')
	resmsg = s.recv(1024)
	print(resmsg.decode('ascii'))
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
			create_user(s)
		elif choice == "2":
			res = att_login(s)
			if res == 0:
				logged_in = True
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


