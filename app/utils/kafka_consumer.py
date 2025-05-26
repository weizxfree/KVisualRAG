import json
from aiokafka import AIOKafkaConsumer, ConsumerRecord
from app.core.config import settings
from app.core.logging import logger
from asyncio import Lock
from app.db.redis import redis
from app.rag.utils import process_file, update_task_progress

KAFKA_TOPIC = settings.kafka_topic
KAFKA_BOOTSTRAP_SERVERS = settings.kafka_broker_url
KAFKA_PRIORITY_HEADER = "priority"
KAFKA_GROUP_ID = settings.kafka_group_id


class KafkaConsumerManager:
    def __init__(self):
        self.consumer = None
        self.lock = Lock()  # 初始化锁
        self.lock_name = "kafka_message_lock"  # Redis锁的名称

    async def start(self):
        if not self.consumer:
            self.consumer = AIOKafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                enable_auto_commit=False,  # 手动提交消息、
            )
            await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def process_message(self, msg: ConsumerRecord):
        

        message = json.loads(msg.value.decode("utf-8"))
        task_id = message["task_id"]
        username = message["username"]
        knowledge_db_id = message["knowledge_db_id"]
        file_meta = message["file_meta"]
        redis_connection = await redis.get_task_connection()
        # 更新任务状态
        await update_task_progress(redis_connection, task_id, "processing", 
            f"Processing {file_meta['original_filename']}...")
        
        # 处理文件
        await process_file(
            redis=redis_connection,
            task_id=task_id,
            username=username,
            knowledge_db_id=knowledge_db_id,
            file_meta=file_meta
        )

    # @retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
    async def consume_messages(self):
        """持续消费Kafka消息."""
        await self.start()
        try:
            async for msg in self.consumer:  # 异步循环消费消息
                logger.info("kafka start consume")
                message_id = msg.offset  # 使用消息的偏移量作为唯一标识
                redis_connection = (
                    await redis.get_task_connection()
                )  # 获取 Redis 连接实例

                lock_key = f"{self.lock_name}:{message_id}"  # 使用偏移量创建唯一的锁名

                # 检查锁是否存在
                is_locked = await redis_connection.exists(lock_key)
                if is_locked:
                    # 如果锁存在，直接进入 else 分支
                    logger.info(
                        f"Message {message_id} is already being processed by another instance."
                    )
                    continue  # 直接跳过此消息，继续处理下一个消息

                lock = redis_connection.lock(lock_key, timeout=100)  # 创建锁

                if await lock.acquire(blocking=False):  # 尝试非阻塞获取锁
                    try:
                        await self.consumer.commit()  # 手动提交消息，确保处理成功才提交
                        await self.process_message(msg)  # 处理每条消息
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                    finally:
                        await lock.release()  # 释放锁
                else:
                    logger.info(
                        f"Message {message_id} is already being processed by another instance."
                    )

        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise e


kafka_consumer_manager = KafkaConsumerManager()
