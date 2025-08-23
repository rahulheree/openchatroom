import datetime
import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default='user', nullable=False)  # Added role for admin status

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    owned_rooms = relationship("Room", back_populates="owner", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="author")
    memberships = relationship("RoomMember", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship("User", back_populates="sessions")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    is_public = Column(Boolean, default=True)
    is_community = Column(Boolean, default=False, nullable=False)  # Added flag for community rooms
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    owner = relationship("User", back_populates="owned_rooms")
    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")
    invites = relationship("RoomInvite", back_populates="room", cascade="all, delete-orphan")

class RoomMember(Base):
    __tablename__ = "room_members"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    unread_count = Column(Integer, default=0)
    
    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="memberships")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    type = Column(String, default="text")
    file_url = Column(String, nullable=True)

    room = relationship("Room", back_populates="messages")
    author = relationship("User", back_populates="messages")

class RoomInvite(Base):
    __tablename__ = "room_invites"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    token = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, index=True)
    
    room = relationship("Room", back_populates="invites")