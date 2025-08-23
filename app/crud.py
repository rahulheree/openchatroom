from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from . import models, schemas
import datetime
from typing import List, Optional
import uuid

async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalars().first()

async def get_user_by_name(db: AsyncSession, name: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).filter(models.User.name == name))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    db_user = models.User(name=user.name)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def create_session(db: AsyncSession, user_id: int, session_id: str) -> models.Session:
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    db_session = models.Session(id=session_id, user_id=user_id, expires_at=expires_at)
    db.add(db_session)
    await db.commit()
    return db_session

async def get_user_by_session_id(db: AsyncSession, session_id: str) -> Optional[models.User]:
    query = (
        select(models.Session)
        .options(selectinload(models.Session.user))
        .filter(models.Session.id == session_id, models.Session.expires_at > datetime.datetime.utcnow())
    )
    result = await db.execute(query)
    session = result.scalars().first()
    return session.user if session else None

async def create_room(db: AsyncSession, room: schemas.RoomCreate, current_user: models.User) -> models.Room:
    is_community_room = (current_user.role == 'admin')
    
    db_room = models.Room(
        name=room.name,
        is_public=room.is_public,
        owner_id=current_user.id,
        is_community=is_community_room
    )
    db.add(db_room)
    await db.commit()
    await db.refresh(db_room)
    await add_user_to_room(db, room_id=db_room.id, user_id=current_user.id)
    await db.refresh(db_room) 
    return db_room

async def get_room(db: AsyncSession, room_id: int) -> Optional[models.Room]:
    result = await db.execute(select(models.Room).filter(models.Room.id == room_id))
    return result.scalars().first()

async def get_room_with_details(db: AsyncSession, room_id: int) -> Optional[models.Room]:
    query = (
        select(models.Room)
        .options(
            selectinload(models.Room.owner),
            selectinload(models.Room.members).selectinload(models.RoomMember.user)
        )
        .filter(models.Room.id == room_id)
    )
    result = await db.execute(query)
    return result.scalars().first()

async def get_community_rooms(db: AsyncSession) -> List[models.Room]:
    query = select(models.Room).filter(models.Room.is_community == True).options(selectinload(models.Room.owner))
    result = await db.execute(query)
    return result.scalars().all()

async def get_userspace_rooms(db: AsyncSession) -> List[models.Room]:
    query = (
        select(models.Room)
        .filter(models.Room.is_public == True, models.Room.is_community == False)
        .options(selectinload(models.Room.owner))
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_rooms(db: AsyncSession, user_id: int) -> List[models.Room]:
    query = (
        select(models.Room)
        .join(models.RoomMember)
        .filter(models.RoomMember.user_id == user_id)
        .options(selectinload(models.Room.owner))
    )
    result = await db.execute(query)
    return result.scalars().all()

async def delete_room(db: AsyncSession, room_id: int) -> Optional[models.Room]:
    db_room = await get_room(db, room_id)
    if db_room:
        await db.delete(db_room)
        await db.commit()
    return db_room

async def add_user_to_room(db: AsyncSession, room_id: int, user_id: int) -> Optional[models.RoomMember]:
    result = await db.execute(
        select(models.RoomMember).filter_by(room_id=room_id, user_id=user_id)
    )
    if result.scalars().first():
        return None  

    db_membership = models.RoomMember(room_id=room_id, user_id=user_id)
    db.add(db_membership)
    await db.commit()
    await db.refresh(db_membership)
    return db_membership

async def remove_user_from_room(db: AsyncSession, room_id: int, user_id: int) -> Optional[models.RoomMember]:
    result = await db.execute(
        select(models.RoomMember).filter_by(room_id=room_id, user_id=user_id)
    )
    db_membership = result.scalars().first()
    if db_membership:
        await db.delete(db_membership)
        await db.commit()
    return db_membership

async def get_room_member(db: AsyncSession, room_id: int, user_id: int) -> Optional[models.RoomMember]:
    result = await db.execute(
        select(models.RoomMember).filter_by(room_id=room_id, user_id=user_id)
    )
    return result.scalars().first()

async def create_message(db: AsyncSession, message: schemas.MessageCreate, room_id: int, user_id: int) -> models.Message:
    db_message = models.Message(
        content=message.content,
        type=message.type,
        file_url=message.file_url,
        room_id=room_id, 
        user_id=user_id
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_messages_for_room(db: AsyncSession, room_id: int, skip: int = 0, limit: int = 50) -> List[models.Message]:
    query = (
        select(models.Message)
        .filter(models.Message.room_id == room_id)
        .order_by(models.Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .options(selectinload(models.Message.author))
    )
    result = await db.execute(query)
    return result.scalars().all()

async def create_room_invite(db: AsyncSession, room_id: int) -> models.RoomInvite:
    db_invite = models.RoomInvite(room_id=room_id)
    db.add(db_invite)
    await db.commit()
    await db.refresh(db_invite)
    return db_invite

async def get_room_by_invite_token_with_owner(db: AsyncSession, token: uuid.UUID) -> Optional[models.Room]:
    query = (
        select(models.Room)
        .join(models.RoomInvite)
        .filter(models.RoomInvite.token == token)
        .options(selectinload(models.Room.owner))
    )
    result = await db.execute(query)
    return result.scalars().first()