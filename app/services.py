import asyncio
import json
import redis.asyncio as redis
from fastapi import WebSocket
from typing import List, Dict, Set
from .settings import settings
from . import schemas

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_to_room(self, room_id: int, message: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

class RedisManager:
    def __init__(self):
        self.redis_conn = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def publish_message(self, room_id: int, message: schemas.Message):
        channel = f"room:{room_id}"
        await self.redis_conn.publish(channel, json.dumps(message.dict(), default=str))

    async def subscribe_to_channel(self, room_id: int, connection_manager: ConnectionManager):
        channel = f"room:{room_id}"
        pubsub = self.redis_conn.pubsub()
        await pubsub.subscribe(channel)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await connection_manager.broadcast_to_room(room_id, message['data'])
            await asyncio.sleep(0.01)

    async def add_active_user(self, room_id: int, user_id: int):
        await self.redis_conn.sadd(f"room:{room_id}:active_users", user_id)
        await self.redis_conn.sadd("global:active_users", user_id)

    async def remove_active_user(self, room_id: int, user_id: int):
        await self.redis_conn.srem(f"room:{room_id}:active_users", user_id)
        await self.redis_conn.srem("global:active_users", user_id)

    async def get_active_users_in_room(self, room_id: int) -> int:
        return await self.redis_conn.scard(f"room:{room_id}:active_users")

    async def get_total_active_users(self) -> int:
        return await self.redis_conn.scard("global:active_users")

connection_manager = ConnectionManager()
redis_manager = RedisManager()