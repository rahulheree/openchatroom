from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime
import uuid

# --- User Schemas ---
class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    role: str
    model_config = ConfigDict(from_attributes=True)

# --- Room Schemas ---
class RoomBase(BaseModel):
    name: str
    is_public: bool = True

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    owner_id: int
    owner: User
    is_community: bool
    model_config = ConfigDict(from_attributes=True)

class RoomMember(BaseModel):
    user: User
    unread_count: int
    model_config = ConfigDict(from_attributes=True)

class RoomDetails(Room):
    members: List[RoomMember]

# --- Message Schemas ---
class MessageBase(BaseModel):
    content: str
    file_url: Optional[str] = None

class MessageCreate(MessageBase):
    type: str = "text"

class Message(MessageBase):
    id: int
    room_id: int
    author: User
    created_at: datetime.datetime
    type: str
    model_config = ConfigDict(from_attributes=True)

# --- Feed and Stats Schemas ---
class PublicRoomFeedItem(Room):
    active_users: int

class MyRoomFeedItem(Room):
    unread_count: int
    active_users: int

class RoomStats(BaseModel):
    active_users: int
    unread_count: int

# --- Token and Invite Schemas ---
class Token(BaseModel):
    join_token: str

class RoomInviteBase(BaseModel):
    token: uuid.UUID

class RoomInviteCreate(RoomInviteBase):
    room_id: int

class RoomInvite(RoomInviteBase):
    room_id: int
    model_config = ConfigDict(from_attributes=True)