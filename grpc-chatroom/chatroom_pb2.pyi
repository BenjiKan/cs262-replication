from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Message(_message.Message):
    __slots__ = ["message", "receiverusername", "senderusername"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECEIVERUSERNAME_FIELD_NUMBER: _ClassVar[int]
    SENDERUSERNAME_FIELD_NUMBER: _ClassVar[int]
    message: str
    receiverusername: str
    senderusername: str
    def __init__(self, senderusername: _Optional[str] = ..., receiverusername: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ["password", "username"]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    password: str
    username: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class UserList(_message.Message):
    __slots__ = ["partialusername"]
    PARTIALUSERNAME_FIELD_NUMBER: _ClassVar[int]
    partialusername: str
    def __init__(self, partialusername: _Optional[str] = ...) -> None: ...

class requestReply(_message.Message):
    __slots__ = ["message", "status"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    message: str
    status: bool
    def __init__(self, status: bool = ..., message: _Optional[str] = ...) -> None: ...