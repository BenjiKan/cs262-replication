# local host IP '127.0.0.1'
HOST = "127.0.0.1"

# Define the port on which you want to connect
PORT = 9182 

# Max message length in characters, as defined in class
# Note that if we use utf-8, this results in a byte
# string that is at most 280 * 4 = 1120 bytes
MAX_MSG_LENGTH = 280
MAX_MSG_CHUNK = 10
# With this, the max message length we can handle is max length * max # of chunks

CLIENT_MESSAGE_APPROVED = b'1'
CLIENT_MESSAGE_REJECTED = b'0'
CLIENT_MESSAGE_SENDING_INFO = b'i'

CLIENT_RETRIEVE_ACCOUNT_LIST = b'a'
CLIENT_ACCOUNT_LIST_NBYTES = 4
CLIENT_ACCOUNT_SENDING = b's'


SERVER_SENDING_MESSAGE  = b'2'


CLIENT_LOGGING_OUT = b'q'