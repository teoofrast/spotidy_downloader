from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import *


async def create_db_engine():
    if DATABASE_TYPE == "sqlite":
        url = f"sqlite+aiosqlite:///{SQLITE_FILENAME}"
        engine = create_async_engine(url)
    else:
        raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")
    return engine

async def create_db_session(engine):
    AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    return AsyncSessionLocal


engine = None
AsyncSessionLocal = None

async def initialize_database():
    global engine
    global AsyncSessionLocal
    engine = await create_db_engine()
    AsyncSessionLocal = await create_db_session(engine)

async def get_db():
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        await initialize_database()
    async with AsyncSessionLocal() as session:
        yield session

async def dispose_database():
    global engine
    if engine:
        await engine.dispose()