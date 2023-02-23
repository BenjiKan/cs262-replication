# CS 262 Design Exercise 1: Wire Protocols

Part 1 (wire protocol) is implemented in the parent directory; part 2 is implemented in the grpc-chatroom sub-directory. We have removed unit tests from this directory.

# Part 1: Wire-Protocol Based Chat App
This is an implementation of a client/server chat application with our own wire protocol.

### Setup
Start the server by running 
```python3 server.py```
Once the server is running, start client(s) by running 
```python3 client.py```

To exit the server or any particular client, use `Ctrl-C`. Our implementation assumes that the server will be up for the entire duration of a desired run, so be sure to terminate all connected clients before exiting.

Once the server and client are running, follow text prompts for further instructions.

## Design Journal

We have implemented an app to comply with the following requirements:
1. Create an account. You must supply a unique user name.
2. List accounts (or a subset of the accounts, by text wildcard)
3. Send a message to a recipient. If the recipient is logged in, deliver immediately; otherwise queue the message and deliver on demand. If the message is sent to someone who isn't a user, return an error message
4. Deliver undelivered messages to a particular user
5. Delete an account. You will need to specify the semantics of what happens if you attempt to delete an account that contains undelivered message.


### Pre-Login UI
Before logging in, the user is able to perform one of 3 tasks: create an account, login to an existing account, or exit. We designed our program such that the server is notified of the client's choice at each step, and facilitates the interaction, with the client acting more so as a means of acquiring input from the user. When creating an account, the client sends the server a username, password, and confirm password. The server checks that the username is still available, the passwords are strong enough (i.e. 6-24 characters), and the user has confirmed their password. If any of these checks fail, the server sends the error messages to the client -- otherwise, a user is created.

Note that creating a user does not automatically log one into the app. We decided to make login a separate process so that multiple users can be created quickly without having to manually log out of each user once created. For login, we have the user input a username and client, before these are sent to the server to be confirmed. If all is well the user is logged in on an individual client; if something fails, the user is notified and they are returned to the pre-login UI.

On the server side, we have an account handler (see `handlers.py`) to manage accounts and store the usernames, passwords, and online status. In addition, when a user logs in through a given client socket, said socket is stored for handling future communication across clients. When a user logs out their status and saved socket is reset.

### Pre-Login Wire Protocol
Since we do not run into concurrency issues with the same socket before we are logged in (we only have a single thread), we use confirmation bytes between the client and server to ensure that data is being sent. To send messages to the server, the client first sends the length of the message and then the message itself. In doing so, the server can use the length of the message to filter out malicious/non-compliant inputs (e.g. by checking if the length is too long from the number of bytes required to encode) and send a rejection byte to the client. When the server sends messages, we also ensure that the server first sends message lengths so that the client knows exactly how many bytes to receive.

### Post-Login UI
Once logged in, the user can send a message, delete their account, list all users according to a Python regex, and logout. For messages, we decided that undelivered messages should be sent upon users becoming online without requiring the user to actively poll for new messages, and when a user is online messages will be shown as they are delivered.

For deleting an account, we opted on deletion to keep messages that have already been sent by the user to others, but prevent other users from sending to them. This affects listing all users (in which case deleted users are not shown), but does not change other functionality.

For listing all users, we allowed the user to input a custom Python regex string that will be parsed and used to check all users. The resulting users will then be sent in the same way (byte-length-data, see below) to the client, which then temporarily stores the names locally and prints it out. 

### Post-Login Wire Protocol
On the client side, we set up live message reception by having a separate thread post-login that handles receiving all messages from the server. Each server message has a leading byte (see `constants.py` for a list on these bytes) that help inform the client on what message is being received. The client code then handles these independently.

Due to concurrency issues, we also changed the way in which servers send messages to the client -- instead of sending the leading byte, message length, and payload in separate `send()` commands, we have the server concatenate these bytestrings into one and send it altogether. Thus, the client code can now peek at the leading bytes, then peek the next few bytes to see the message size, and extract the message. This helps ensure that `recv` calls on the client side do not end up absorbing more data than intended (e.g. having a `recv(1024)` for a message that in total is only 50 bytes long could unintentionally absorb other messages coming in via the same socket). The client listener thread also puts client-handling messages into a queue (with thread locks to ensure no race conditions) that the non-listening thread can obtain responses from.

# Part 2: gRPC-based Chat App
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

# Comparisons between the wire protocol and gRPC
Compared to the wire protocol implementation, the gRPC implementation is much simpler and easier to read, since the gRPC module takes care of the details of connection. Indeed, the `chatroom.proto` file provides a succinct overview of different methods and their relationships, which are implemented in slightly more detail in `chatroom_server.py` and `chatroom_client.py`. 

Usage is also easier, as we use single-word commands with follow-up prompts for parameters.

The performance of the gRPC and wire protocol are similar, although the UI of the wire protocol is more detailed and that implementation has additional features. We hoped the gRPC version would be a "lite" version of the service, with implementation as lightweight as possible within reason to offset the additional weight of the communication and protocol buffers. 

The protocol buffers in the wire protocol are much smaller and simpler as well, as each buffer contains just the necessary arguments with minimal metadata overhead. On the other hand, arguments are simpler but protocol buffers for the gRPC implementation are larger, as the gRPC module takes care of all the low-level metadata issues.