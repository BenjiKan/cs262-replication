# CS 262 Design Exercise 3: Replication
This is an implementation of a client/server chat application with the gRPC framework, satisfying the properties of [Persistence](#p) and 2-[Fault Tolerance](#ft).

The design journal for the original gRPC-based chat app is in the corresponding section [gRPC-based Chat App](#gRPC) below, including installation and setup instructions.

## Fault Tolerance
a

## Persistence
a

# gRPC-based Chat App
This is an implementation of a client/server chat application with the gRPC framework.

### Dependencies
Make sure to install the `grpc` module, following instructions: https://grpc.io/docs/languages/python/quickstart/. Use `python3` if possible. 

You may also need to run
```
pip install inputimeout
```
if you do not already have the package `inputimeout` already installed.

### Setup
#### Starting the application
From the parent directory, enter the grpc-chatroom directory.
```
cd grpc-chatroom
```

Start the server by running
```
python3 chatroom_server.py

```
and the client by running
```
python3 chatroom_client.py

```
To exit the server or any particular client, use `Ctrl-C`. Our implementation assumes that the server will be up for the entire duration of a desired run, so be sure to terminate all connected clients before exiting.


#### Interacting with the application.
The server does not take any input; it will occassionally print output logs for reference. All commands take place in the client; one can simply follow the prompts after starting it. The list of commands is as follows:

```
help
```
Prints help menu.

```
create
```
Create an account, supplying username and password.

```
login
```
If not already logged in, log in with username and password.

```
logout
```
Logout of account.

```
list
```
List all accounts that partially match entered partial username.

```
delete
```
Delete account.

```
send
```
Send message to another user, via server.

```
check
```
Check for messages; automatically called and running in background once logged in.
```
quit
```
Quit the program.


## Design Journal
The gRPC implementation of the design specs is titled "ChatRoom," and provides a client-server chat application using the gRPC package. The primary design principle is to create a simple, lightweight (yet functional) application. In particular, we remove some additional fucntionalities provided by the wire protocol. For lightweight running, we attempt to minimize computation done on the client-side (assuming the server will have more compute power and uptime). The only major client-side computation/storage is keeping track of whether the curent client is logged in.

Beginning with account creation, we do not require a confirmation of password; simply supplying a username and password is sufficient. This enables the most simple rpc protocol possible, while also reducing computations done by the client.

Upon login, the client immediately updates its own logged_in status, and the server also keeps track of the logged in users. Additionally, the client begins a response stream to listen for messages that may be queued by the server or might be sent in the future on a separate thread.

The logout feature updates the status on both client and server side via the stub, which alters how messages are sent and received. In addition to manual log out, we also have a timeout condition, where if a command is not entered in 60 seconds an account is automatically logged out.

Deleting a user requires one to be logged in; this prevents the case that undelievered messages have to be dealt with when an account is deleted. We do request a confirmatin on the client side for deletion, since this is a much more permanent action.


One can list all users without even being logged in (this is one of the few functions that can be called without a login), as this allows for one who has forgotten their username to figure it out without authentication, and to see who else might be using the chat service. We have an automatic partial match for username, so as long as some username begins with the partial string entered. If no string is entered, all accounts will be returned.

One can send messages to any other existing user, but not oneself—we did not believe that functionality would be useful. To deliver a message, it is passed into a queue on the server side, from which each client listens for messages corresponding to their username. Delivery of the message includes a text prefix that indicates the sending user.
