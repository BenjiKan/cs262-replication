# CS 262 Design Exercise 3: Replication
This is an implementation of a client/server chat application with the gRPC framework, satisfying the properties of [Persistence](#persistence) and 2-[Fault Tolerance](#fault-tolerance).

The design journal for the original gRPC-based chat app is in the corresponding section [gRPC-based Chat App](#grpc-based-chat-app) below, including installation and setup instructions.

TODO: setup with 3 different terminals

## Fault Tolerance
Our fault-tolerant chat system is based on a primary-backup model. Most intuitively, this model involves one primary server and several backup replica servers: clients only communicate with the primary server, which backs up all operations and states on the backup servers. If the primary fails, then one of the backup servers becomes the new primary, which all clients now communicate with. In order to achieve 2-fault tolerance, we need at least three servers; this is hard-coded as a constant in `chatroom_server.py` but the architecture is flexible and this can be adjusted for higher fault tolerance.

If any one or two of the three servers die, the chat system reamins intact. These faults are not observable by clients: due to the hierarchical structure of the primary-backup model, backup failures do not affect anything in the client connection (since they only communicate with the primary server), and if the primary fails, we have a protocol to automatically redirect clients to the new primary. This can be tested by using `Ctrl-D` to exit a thread, thus killing one of the servers: one can choose any of the three servers to kill and observe the host switching on the client-side.

Our leader election protocol is simple: we will default to have whichever live server has the lowest port number as the primary. The current implementation spins up parallel server processes from the same machine, each inhabiting a distinct port number, so there will be no conflict (note that this system can easily be generalized to have each server supported on a different machine; for the sake of demonstration we focus on the simple model where everything is hosted on the same machine). Moreover, each server is aware of how many other replicas there are, and their intra-server communication will allow them to recognize which other servers are alive, and thus which is indisputedly the primary. The server ports, both externally for connection to clients and internally with each other, are defined in `constants.py`. This agreement extends to the clients, so that there is no mistake about which server is the primary. If a client attempts to communicate with a server that is not the primary, it will be blocked and then redirected until the request reaches the true (new) primary. Note that this implementation does not support a single dead replica rejoining; see the section on [Persistence](#persistence) for discussion of how to ensure backend persistence when the entire system goes down.

Despite its intuitive simplicity, the central drawback of the primary-backup model is that all communication must go through the same central server that is serving as the primary, which results in increased latency if it must handle many client connections. For a small number of clients, however, the primary-backup model works well and is easy to debug. As the system scales, it becomes more reasonable to use a paxos-style consensus algorithm among all the equivalent replica servers, allowing for any client to connect to any replica server, which enables better load-balancing.


## Persistence
Our system is persistent; that is, if the entire server group goes down, it can be brought up without loss of unsent messages. We achieve this property using logs as in the standard process proposed by the Schneider paper on the primary-backup approach. Each replica maintains its own log, so that if a backup becomes a primary, the system continues to function.

In order for the logs to remain consistent, the primary first receives a request from a client, performs the update on its own state database (e.g. creating an account), then forwards that request to the replicas, and finally it updates and flushes the log. In this way, the logs will remain consistent even if the primary goes down at any point. Backups also perform state updates before logging, so that the log will only record committed requests.

Upon system restart, each server will follow its respective log until it reaches the end, thus attaining its previous state before shutdown. Then, the servers communicate to figure out which will be the primary: since the logs are ordered as state machines, whichever has the longest log will have the most recent updates and becomes primary. Ties are broken by the lowest port number, as before. At this point, the server is ready to continue, and clients which log in will be able to receive undelivered messages from their queue. 


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
The gRPC implementation of the design specs is titled "ChatRoom," and provides a client-server chat application using the gRPC package. The primary design principle is to create a simple, lightweight (yet functional) application. In particular, we remove some additional functionalities provided by the original wire protocol. For lightweight running, we attempt to minimize computation done on the client-side (assuming the server will have more compute power and uptime). The only major client-side computation/storage is keeping track of whether the curent client is logged in.

Beginning with account creation, we do not require a confirmation of password; simply supplying a username and password is sufficient. This enables the most simple rpc protocol possible, while also reducing computations done by the client.

Upon login, the client immediately updates its own logged_in status, and the server also keeps track of the logged in users. Additionally, the client begins a response stream to listen for messages that may be queued by the server or might be sent in the future on a separate thread.

The logout feature updates the status on both client and server side via the stub, which alters how messages are sent and received. In addition to manual log out, we also have a timeout condition, where if a command is not entered in 60 seconds an account is automatically logged out.

Deleting a user requires one to be logged in; this prevents the case that undelievered messages have to be dealt with when an account is deleted. We do request a confirmatin on the client side for deletion, since this is a much more permanent action.


One can list all users without even being logged in (this is one of the few functions that can be called without a login), as this allows for one who has forgotten their username to figure it out without authentication, and to see who else might be using the chat service. We have an automatic partial match for username, so as long as some username begins with the partial string entered. If no string is entered, all accounts will be returned.

One can send messages to any other existing user, but not oneself—we did not believe that functionality would be useful. To deliver a message, it is passed into a queue on the server side, from which each client listens for messages corresponding to their username. Delivery of the message includes a text prefix that indicates the sending user.
