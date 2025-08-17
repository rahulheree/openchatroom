# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.api import router as api_router

# # --- ADDED IMPORTS ---
# # Import the database engine and the Base for table creation
# from app.database import engine
# from app.models import Base

# # --- ADDED FUNCTION ---
# # This async function will connect to the database and create all tables
# # defined in your models.py file. It will not delete or modify existing tables.
# async def create_db_and_tables():
#     async with engine.begin() as conn:
#         # This line does the magic. It creates tables based on your SQLAlchemy models.
#         await conn.run_sync(Base.metadata.create_all)


# app = FastAPI(title="Real-Time Chat App")

# # --- ADDED STARTUP EVENT ---
# # This tells FastAPI to run the `create_db_and_tables` function
# # exactly once when the application starts up.
# @app.on_event("startup")
# async def on_startup():
#     await create_db_and_tables()


# # Add CORS middleware if your frontend is on a different domain
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Replace with your frontend URL in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(api_router, prefix="/api/v1")

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the Chat API"}

# # The comment below was in your original file and is still relevant.
# # Add startup/shutdown events for Redis if needed,
# # though redis-py handles connection pooling automatically.

# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import Base
from app.api import router as api_router

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(title="Real-Time Chat App")

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

# This is the corrected CORS middleware block.
# It specifically allows your frontend to connect and use cookies.
origins = [
    "http://localhost",
    "http://localhost:5173", # The default address for Vite React apps
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allow specific origins
    allow_credentials=True, # This is crucial for cookies
    allow_methods=["*"],    # Allow all methods
    allow_headers=["*"],    # Allow all headers
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Chat API"}