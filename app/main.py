import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.logging import logger
from app.framework.app_framework import FastAPIFramework


from app.db.mysql_session import mysql
from app.db.mongo import mongodb
from app.db.redis import redis
from app.db.miniodb import async_minio_manager
from app.utils.kafka_producer import kafka_producer_manager
from app.utils.kafka_consumer import kafka_consumer_manager

# 创建 FastAPIFramework 实例
framework = FastAPIFramework(debug_mode=settings.debug_mode)

# 获取 FastAPI 应用实例
app = framework.get_app()

# CORS settings
origins = [
    "*"
]  # ["https://your-frontend-domain.com"],  # 建议生产环境中替换为具体的域名白名单

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动事件处理代码可以放在这里
    # logger.info("FastAPI Started")
    await mongodb.connect()  # 连接 MongoDB
    await kafka_producer_manager.start()  # 启动Kafka生产者
    await async_minio_manager.init_minio()
    # await kafka_consumer_manager.start()  # 启动Kafka消费者
    asyncio.create_task(kafka_consumer_manager.consume_messages())  # 启动Kafka消费者

    yield
    # 关闭事件处理代码可以放在这里
    await kafka_producer_manager.stop()  # 停止Kafka生产者
    # await kafka_consumer_manager.stop()  # 停止Kafka消费者
    await mysql.close()  # 关闭 MySQL 连接
    await mongodb.close()  # 关闭 MongoDB 连接
    await redis.close()  # 关闭 Redis 连接
    logger.info("FastAPI Closed")


app.router.lifespan_context = lifespan

# 路由
framework.include_router(api_router)

logger.info("FastAPI app started with settings: %s", settings)
