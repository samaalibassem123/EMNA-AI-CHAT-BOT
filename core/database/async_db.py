from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, expire_on_commit=False )

async def get_db()->AsyncGenerator[AsyncSession,None]:
    async with async_session() as session:
        yield session



