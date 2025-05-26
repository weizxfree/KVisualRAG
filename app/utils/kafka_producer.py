import json
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from app.core.config import settings
from app.core.logging import logger

KAFKA_TOPIC = settings.kafka_topic
KAFKA_BOOTSTRAP_SERVERS = settings.kafka_broker_url
KAFKA_PRIORITY_HEADER = "priority"


class KafkaProducerManager:
    def __init__(self):
        self.producer = None

    async def start(self):
        if not self.producer:
            self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
            await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    # @retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
    async def send_embedding_task(
        self,
        task_id: str,
        username: str,
        knowledge_db_id: str,
        file_meta: dict,
        priority: str,
    ):

        message = {
            "task_id": task_id,
            "username": username,
            "knowledge_db_id": knowledge_db_id,
            "file_meta": file_meta,
        }

        try:
            await self.start()
            await self.producer.send(
                KAFKA_TOPIC,
                json.dumps(message).encode("utf-8"),
                headers=[
                    (KAFKA_PRIORITY_HEADER, str(priority).encode("utf-8"))
                ],  # 消息头包含优先级
            )
            logger.info(f"Task {task_id} message sent to Kafka: {message} with priority: {priority}")
        except KafkaError as e:
            logger.error(f"Error sending message to Kafka: {e}")


kafka_producer_manager = KafkaProducerManager()
