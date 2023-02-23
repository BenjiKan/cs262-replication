# Part 1: Wire-Protocol Based Chat App
This is an implementation with our own wire protocol.

### Setup
Start the server by running `python3 server.py`. Once the server is running, start clients by running `python3 client.py`.

To exit the server, use `Ctrl-C`. Be sure to terminate all connected clients before exiting the server.

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