import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Response, WebSocket, WebSocketDisconnect, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import os
import shutil
from . import crud, schemas, models, security, services
from .deps import get_db, get_current_user

router = APIRouter()

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/session/start", response_model=schemas.User)
async def start_session(response: Response, user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_name(db, name=user_in.name)
    if not user:
        user = await crud.create_user(db, user=user_in)
    
    session_id = security.create_session_id()
    await crud.create_session(db, user_id=user.id, session_id=session_id)
    
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, secure=False, samesite="lax"
    )
    return user

@router.get("/session/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/rooms", response_model=schemas.Room, status_code=status.HTTP_201_CREATED)
async def create_room(
    room: schemas.RoomCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud.create_room(db=db, room=room, current_user=current_user)

@router.get("/rooms/community", response_model=List[schemas.PublicRoomFeedItem])
async def list_community_rooms(db: AsyncSession = Depends(get_db)):
    rooms = await crud.get_community_rooms(db)
    feed = []
    for room in rooms:
        active_users = await services.redis_manager.get_active_users_in_room(room.id)
        feed.append(schemas.PublicRoomFeedItem(**room.__dict__, active_users=active_users))
    return feed

@router.get("/rooms/userspaces", response_model=List[schemas.PublicRoomFeedItem])
async def list_userspace_rooms(db: AsyncSession = Depends(get_db)):
    rooms = await crud.get_userspace_rooms(db)
    feed = []
    for room in rooms:
        active_users = await services.redis_manager.get_active_users_in_room(room.id)
        feed.append(schemas.PublicRoomFeedItem(**room.__dict__, active_users=active_users))
    return feed

@router.get("/rooms/my", response_model=List[schemas.MyRoomFeedItem])
async def list_my_rooms(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rooms = await crud.get_user_rooms(db, user_id=current_user.id)
    feed = []
    for room in rooms:
        active_users = await services.redis_manager.get_active_users_in_room(room.id)
        member_info = await crud.get_room_member(db, room_id=room.id, user_id=current_user.id)
        unread_count = member_info.unread_count if member_info else 0
        feed.append(
            schemas.MyRoomFeedItem(
                **room.__dict__,
                active_users=active_users,
                unread_count=unread_count
            )
        )
    return feed

@router.get("/rooms/{room_id}", response_model=schemas.RoomDetails)
async def get_room_details(room_id: int, db: AsyncSession = Depends(get_db)):
    room = await crud.get_room_with_details(db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    room = await crud.get_room(db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this room")
    await crud.delete_room(db, room_id=room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/rooms/{room_id}/join", status_code=status.HTTP_201_CREATED)
async def join_room(
    room_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    room = await crud.get_room(db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    membership = await crud.add_user_to_room(db, room_id=room_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=400, detail="User is already a member of this room")
    return {"status": "joined room successfully"}

@router.post("/rooms/{room_id}/leave", status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    membership = await crud.remove_user_from_room(db, room_id=room_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of this room")
    return {"status": "left room successfully"}

@router.get("/rooms/{room_id}/members", response_model=List[schemas.User])
async def list_room_members(room_id: int, db: AsyncSession = Depends(get_db)):
    room = await crud.get_room_with_details(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return [member.user for member in room.members]

@router.get("/rooms/{room_id}/messages", response_model=List[schemas.Message])
async def get_room_messages(
    room_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_messages_for_room(db, room_id=room_id, skip=skip, limit=limit)

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    db: AsyncSession = Depends(get_db),
):
    session_id = websocket.cookies.get("session_id")
    if not session_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user = await crud.get_user_by_session_id(db, session_id)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    membership = await crud.get_room_member(db, room_id, user.id)
    if not membership:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not a member of this room")
        return

    await services.connection_manager.connect(websocket, room_id)
    await services.redis_manager.add_active_user(room_id, user.id)
    
    redis_listener_task = asyncio.create_task(
        services.redis_manager.subscribe_to_channel(room_id, services.connection_manager)
    )

    try:
        while True:
            data = await websocket.receive_text()
            message_data = schemas.MessageCreate.model_validate_json(data)
            
            db_message = await crud.create_message(
                db, 
                message=message_data, 
                room_id=room_id, 
                user_id=user.id
            )
            await db.refresh(db_message, attribute_names=['author'])
            
            await services.redis_manager.publish_message(room_id, schemas.Message.from_orm(db_message))

    except WebSocketDisconnect:
        services.connection_manager.disconnect(websocket, room_id)
        await services.redis_manager.remove_active_user(room_id, user.id)
        if not redis_listener_task.done():
            redis_listener_task.cancel()

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    unique_filename = f"{uuid.uuid4()}-{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_url = f"/uploaded_files/{unique_filename}"
    
    return {"file_url": file_url}

@router.post("/rooms/{room_id}/invite", response_model=schemas.RoomInvite)
async def generate_invite_link(
    room_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    room = await crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only room owners can create invite links")
        
    invite = await crud.create_room_invite(db, room_id)
    return invite

@router.get("/invite/{token}", response_model=schemas.Room)
async def get_room_by_invite(
    token: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    room = await crud.get_room_by_invite_token_with_owner(db, token)
    if not room:
        raise HTTPException(status_code=404, detail="Invalid invite token")

    return room

