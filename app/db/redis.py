import aioredis
from app.core.config import settings


class Redis:
    def __init__(self):
        self.redis_pools = {}

    def get_redis_pool(self, db: int):
        if db not in self.redis_pools:
            self.redis_pools[db] = aioredis.ConnectionPool.from_url(
                f"redis://:{settings.redis_password}@{settings.redis_url}",
                decode_responses=True,
                db=db,
            )
        return self.redis_pools[db]

    async def get_redis_connection(self, db: int = 0):
        pool = self.get_redis_pool(db)
        return aioredis.Redis(connection_pool=pool)

    async def get_token_connection(self):
        return await self.get_redis_connection(settings.redis_token_db)

    async def get_task_connection(self):
        return await self.get_redis_connection(settings.redis_task_db)

    async def get_lock_connection(self):
        return await self.get_redis_connection(settings.redis_lock_db)

    async def close(self):
        for pool in self.redis_pools.values():
            await pool.disconnect()


redis = Redis()
