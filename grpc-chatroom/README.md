# Part 2
This is a client-server application built using the gRPC framework.

## Dependencies
Make sure to install the `grpc` module, following instructions: https://grpc.io/docs/languages/python/quickstart/

## Setup
Enter the grpc directory.
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

The server does not take any input; it will occassionally print output logs for reference. All commands take place in the client; one can simply follow the prompts after starting it. The list of commands is as follows:

```
quit
```
Quit the program.

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


# Design Journal
The gRPC implementation of the design specs is titled "ChatRoom," and provides a client-server chat application using the gRPC package. The primary design principle is to create a simple, lightweight (yet functional) application. In particular, we remove some additional fucntionalities provided by the wire protocol. For lightweight running, we attempt to minimize computation done on the client-side (assuming the server will have more compute power and uptime). The only major client-side computation/storage is keeping track of whether the curent client is logged in.

Beginning with account creation, we do not require a confirmation of password; simply supplying a username and password is sufficient. This enables the most simple rpc protocol possible, while also reducing computations done by the client.

Upon login, the client immediately updates its own logged_in status, and the server also keeps track of the logged in users. Additionally, the client begins a response stream to listen for messages that may be queued by the server or might be sent in the future on a separate thread.

The logout feature updates the status on both client and server side via the stub, which alters how messages are sent and received. In addition to manual log out, we also have a timeout condition, where if a command is not entered in 30 seconds an account is automatically logged out.

Deleting a user requires one to be logged in; this prevents the case that undelievered messages have to be dealt with when an account is deleted. We do request a confirmatin on the client side for deletion, since this is a much more permanent action.


One can list all users without even being logged in (this is one of the few functions that can be called without a login), as this allows for one who has forgotten their username to figure it out without authentication, and to see who else might be using the chat service. We have an automatic partial match for username, so as long as some username begins with the partial string entered. If no string is entered, all accounts will be returned.

One can send messages to any other existing user, but not oneself—we did not believe that functionality would be useful. To deliver a message, it is passed into a queue on the server side, from which each client listens for messages corresponding to their username. Delivery of the message includes a text prefix that indicates the sending user.

# Comparisons
Compared to the wire protocol implementation, the gRPC implementation is much simpler and easier to read, since the gRPC module takes care of the details of connection. Indeed, the chatroom.proto file provides a succinct overview of different methods and their relationships, which are implemented in slightly more detail in chatroom_server.py and chatroom_client.py. 

Usage is also easier, as we use single-word commands with follow-up prompts for parameters.

The performance of the gRPC and wire protocol are similar, although the UI of the wire protocol is more detailed and that implementation has additional features. We hoped the gRPC version would be a "lite" version of the service, with implementation as lightweight as possible within reason to offset the additional weight of the communication and protocol buffers. 

The protocol buffers in the wire protocol are much smaller and simpler as well, as each buffer contains just the necessary arguments with minimal metadata overhead. On the other hand, arguments are simpler but protocol buffers for the gRPC implementation are larger, as the gRPC module takes care of all the low-level metadata issues.