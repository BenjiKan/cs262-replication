from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Account(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class AccountID(_message.Message):
    __slots__ = ["id", "reply"]
    ID_FIELD_NUMBER: _ClassVar[int]
    REPLY_FIELD_NUMBER: _ClassVar[int]
    id: int
    reply: requestReply
    def __init__(self, id: _Optional[int] = ..., reply: _Optional[_Union[requestReply, _Mapping]] = ...) -> None: ...

class AccountName(_message.Message):
    __slots__ = ["name", "reply"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    REPLY_FIELD_NUMBER: _ClassVar[int]
    name: str
    reply: requestReply
    def __init__(self, name: _Optional[str] = ..., reply: _Optional[_Union[requestReply, _Mapping]] = ...) -> None: ...

class Text(_message.Message):
    __slots__ = ["reply", "text"]
    REPLY_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    reply: requestReply
    text: str
    def __init__(self, text: _Optional[str] = ..., reply: _Optional[_Union[requestReply, _Mapping]] = ...) -> None: ...

class listAccounts(_message.Message):
    __slots__ = ["reply"]
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: requestReply
    def __init__(self, reply: _Optional[_Union[requestReply, _Mapping]] = ...) -> None: ...

class requestReply(_message.Message):
    __slots__ = ["reply"]
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: str
    def __init__(self, reply: _Optional[str] = ...) -> None: ...

class sendText(_message.Message):
    __slots__ = ["receiverID", "senderID", "text"]
    RECEIVERID_FIELD_NUMBER: _ClassVar[int]
    SENDERID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    receiverID: int
    senderID: int
    text: str
    def __init__(self, senderID: _Optional[int] = ..., receiverID: _Optional[int] = ..., text: _Optional[str] = ...) -> None: ...
