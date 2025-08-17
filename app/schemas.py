from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime

# User Schemas
class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Room Schemas
class RoomBase(BaseModel):
    name: str
    is_public: bool = True

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    owner_id: int
    owner: User
    model_config = ConfigDict(from_attributes=True)

class RoomMember(BaseModel):
    user: User
    unread_count: int
    model_config = ConfigDict(from_attributes=True)

class RoomDetails(Room):
    members: List[RoomMember]

# Message Schemas
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    room_id: int
    author: User
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# Feed/Stats Schemas
class PublicRoomFeedItem(Room):
    active_users: int

class MyRoomFeedItem(Room):
    unread_count: int
    active_users: int

class RoomStats(BaseModel):
    active_users: int
    unread_count: int

# Session Schemas
class Token(BaseModel):
    join_token: str