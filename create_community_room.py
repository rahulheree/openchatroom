import asyncio
from app.database import AsyncSessionLocal
from app import crud, schemas, models

async def create_community_room_script():
    async with AsyncSessionLocal() as db:
        try:
            mock_admin_user = models.User(id=1, name="admin-user-placeholder", role="admin")
            new_room_data = schemas.RoomCreate(name="My First Community Room", is_public=True)
            created_room = await crud.create_room(
                db=db,
                room=new_room_data,
                current_user=mock_admin_user
            )
            
            print(f"✅ Successfully created community room: {created_room.name}")
            print(f"   ID: {created_room.id}")

        except Exception as e:
            print(f"❌ An error occurred: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(create_community_room_script())