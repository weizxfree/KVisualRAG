from typing import List
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.db.redis import redis
from app.models.conversation import (
    ConversationCreate,
    ConversationOutput,
    ConversationRenameInput,
    ConversationSummary,
    ConversationUpdateModelConfig,
)
from app.models.user import User
from app.db.mongo import MongoDB, get_mongo
from app.core.security import get_current_user, verify_username_match
from app.rag.convert_file import save_file_to_minio
from app.utils.kafka_producer import kafka_producer_manager
from app.core.logging import logger
from app.db.milvus import milvus_client

router = APIRouter()


# 创建新会话
@router.post("/conversations", response_model=dict)
async def create_conversation(
    conversation: ConversationCreate,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(
        current_user, conversation.conversation_id.split("_")[0]
    )
    await db.create_conversation(
        conversation_id=conversation.conversation_id,
        username=conversation.username,
        conversation_name=conversation.conversation_name,
        model_config=conversation.chat_model_config,
    )
    return {"status": "success"}


# 修改会话名称
@router.post("/conversations/rename", response_model=dict)
async def re_name(
    renameInput: ConversationRenameInput,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, renameInput.conversation_id.split("_")[0])

    result = await db.update_conversation_name(
        renameInput.conversation_id, renameInput.conversation_new_name
    )
    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


# 修改会话数据库使用
@router.post("/conversations/config", response_model=dict)
async def select_bases(
    basesInput: ConversationUpdateModelConfig,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, basesInput.conversation_id.split("_")[0])

    result = await db.update_conversation_model_config(
        basesInput.conversation_id, basesInput.chat_model_config
    )
    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


# 获取指定 conversation_id 的完整会话记录
@router.get("/conversations/{conversation_id}", response_model=ConversationOutput)
async def get_conversation(
    conversation_id: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, conversation_id.split("_")[0])
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_files = []
    for turn in conversation["turns"]:
        user_files.append(await db.get_files_by_knowledge_base_id(turn["temp_db"]))

    return {
        "conversation_id": conversation["conversation_id"],
        "conversation_name": conversation["conversation_name"],
        "chat_model_config": conversation["model_config"],
        "username": conversation["username"],
        "turns": [
            {
                "message_id": turn["message_id"],
                "parent_message_id": turn["parent_message_id"],
                "user_message": turn["user_message"],
                "user_file": user_file,
                "temp_db": turn["temp_db"],
                "ai_message": turn["ai_message"],
                "file_used": turn["file_used"],
                "status": turn["status"],
                "timestamp": turn["timestamp"].isoformat(),
                "total_token": turn["total_token"],
                "completion_tokens": turn["completion_tokens"],
                "prompt_tokens": turn["prompt_tokens"],
            }
            for turn, user_file in zip(conversation["turns"], user_files)
        ],
        "created_at": conversation["created_at"].isoformat(),
        "last_modify_at": conversation["last_modify_at"].isoformat(),
    }


# 查询指定用户的所有会话
@router.get("/users/{username}/conversations", response_model=List[ConversationSummary])
async def get_conversations_by_user(
    username: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, username)
    conversations = await db.get_conversations_by_user(username)
    if not conversations:
        return []
    return [
        {
            "conversation_id": conversation["conversation_id"],
            "conversation_name": conversation["conversation_name"],
            "chat_model_config": conversation["model_config"],
            "is_read": conversation["is_read"],
            "created_at": conversation["created_at"].isoformat(),
            "last_modify_at": conversation["last_modify_at"].isoformat(),
        }
        for conversation in conversations
    ]


# 删除指定会话
@router.delete("/conversations/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, conversation_id.split("_")[0])
    result = await db.delete_conversation(conversation_id)
    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# 删除指定用户的所有会话
@router.delete("/users/{username}/conversations", response_model=dict)
async def delete_all_conversations_by_user(
    username: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    # 验证当前用户是否与要删除的用户名匹配
    await verify_username_match(current_user, username)

    # 执行批量删除
    result = await db.delete_all_conversation(username)

    # 检查删除结果并返回响应
    """if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="No conversations found for this user or already deleted",
        )"""

    return result


# 上传文件
@router.post("/upload/{username}/{conversation_id}", response_model=dict)
async def upload_multiple_files(
    files: List[UploadFile],
    username: str,
    conversation_id: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):

    # 验证当前用户是否与要删除的用户名匹配
    await verify_username_match(current_user, username)
    return_files = []
    knowledge_db_id = "temp_" + conversation_id
    await db.create_knowledge_base(
        username,
        f"temp_base_{username}",
        knowledge_db_id,
        True,
    )
    if not milvus_client.check_collection(
        "colqwen" + knowledge_db_id.replace("-", "_")
    ):
        milvus_client.create_collection("colqwen" + knowledge_db_id.replace("-", "_"))
    # 生成任务ID
    task_id = username + "_" + str(uuid.uuid4())
    total_files = len(files)
    redis_connection = await redis.get_task_connection()
    # 初始化任务状态
    await redis_connection.hset(
        f"task:{task_id}",
        mapping={
            "status": "processing",
            "total": total_files,
            "processed": 0,
            "message": "Initializing file processing...",
        },
    )
    await redis_connection.expire(f"task:{task_id}", 3600)  # 1小时过期

    # 保存文件元数据并准备Kafka消息
    file_meta_list = []
    for file in files:
        # 保存文件到MinIO
        minio_filename, minio_url = await save_file_to_minio(username, file)

        # 生成文件ID并保存元数据
        file_id = f"{username}_{uuid.uuid4()}"
        await db.create_files(
            file_id=file_id,
            username=username,
            filename=file.filename,
            minio_filename=minio_filename,
            minio_url=minio_url,
            knowledge_db_id=knowledge_db_id,
        )
        res = await db.knowledge_base_add_file(
            knowledge_base_id=knowledge_db_id,
            file_id=file_id,
            original_filename=file.filename,
            minio_filename=minio_filename,
            minio_url=minio_url,
        )

        file_meta_list.append(
            {
                "file_id": file_id,
                "minio_filename": minio_filename,
                "original_filename": file.filename,
            }
        )
        return_files.append(
            {
                "id": file_id,
                "minio_filename": minio_filename,
                "filename": file.filename,
                "url": minio_url,
            }
        )

    # 发送Kafka消息（每个文件一个消息）
    for meta in file_meta_list:
        logger.info(
            "send {task_id} to kafka, file name {file.filename}, knowledge id {knowledge_db_id}."
        )
        await kafka_producer_manager.send_embedding_task(
            task_id=task_id,
            username=username,
            knowledge_db_id=knowledge_db_id,
            file_meta=meta,
            priority=1,
        )

    return {
        "task_id": task_id,
        "knowledge_db_id": knowledge_db_id,
        "files": return_files,
    }
