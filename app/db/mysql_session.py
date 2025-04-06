from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator


class MySQL:
    def __init__(self):
        self.engine = create_async_engine(
            settings.db_url,
            echo=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
        )
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session() as session:
            yield session

    async def close(self):
        await self.engine.dispose()


mysql = MySQL()


async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in mysql.get_session():
        yield session
