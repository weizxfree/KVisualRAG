from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_version_url: str = "/api/v1"
    max_workers: int = 10
    log_level: str = "INFO"
    log_file: str = "app.log"
    db_url: str = "mysql+asyncmy://username:password@localhost/dbname"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    redis_url: str = "localhost:6379"
    redis_password: str = "redisdspw"
    redis_token_db: int = 0  # 用于token存储
    redis_task_db: int = 1  # 用于存储embedding任务队列
    redis_lock_db: int = 2  # 用于存储embedding任务队列
    secret_key: str = "your_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 8  # 8 days
    mongodb_url: str = "localhost:27017"
    mongodb_db: str = "chat_mongodb"
    mongodb_root_username: str = "testuser"
    mongodb_root_password: str = "testpassword"
    mongodb_pool_size: int = 100  # MongoDB 最大连接池大小
    mongodb_min_pool_size: int = 10  # MongoDB 最小连接池大小
    debug_mode: bool = False
    kafka_broker_url: str = "localhost:9094"
    kafka_topic: str = "task_generation"
    kafka_group_id: str = "task_consumer_group"
    # kafka_priority_levels: int = 5  # 定义优先级的级别（0为最高）
    minio_url: str = "http://localhost:9110"  # MinIO 服务的URL
    minio_access_key: str = "your_access_key"  # MinIO 的访问密钥
    minio_secret_key: str = "your_secret_key"  # MinIO 的密钥
    minio_bucket_name: str = "ai-chat"  # 需要上传的桶的名称
    milvus_uri:str ="http://127.0.0.1:19530"
    colbert_model_path:str = "/home/administrator/KnowFlowVisualRAG/colqwen2.5-v0.2"

    class Config:
        env_file = ".env"
        env_prefix = "APP_"


settings = Settings()
# print(settings.mongodb_url)  # 这里应只打印 "localhost:27017"
