import asyncio
import json
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.core.security import get_current_user, verify_username_match
from app.db.redis import redis
from app.models.conversation import UserMessage
from app.models.user import User
from app.rag.llm_service import ChatService
import uuid

router = APIRouter()


# 创建新会话
@router.post("/chat", response_model=dict)
async def chat_stream(
    user_message: UserMessage,
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(
        current_user, user_message.conversation_id.split("_")[0]
    )

    message_id = str(uuid.uuid4())  # 生成 UUIDv4

    return StreamingResponse(
        ChatService.create_chat_stream(user_message, message_id),
        media_type="text/event-stream",
        headers={"conversation-id": user_message.conversation_id},
    )


# SSE进度查询接口
@router.get("/task/{username}/{task_id}")
async def get_task_progress(
    task_id: str,
    username: str,
    current_user: User = Depends(get_current_user),
):

    # 验证当前用户是否与要删除的用户名匹配
    await verify_username_match(current_user, username)
    redis_connection = await redis.get_task_connection()

    async def event_generator():
        retries = 5
        while retries > 0:
            task_data = await redis_connection.hgetall(f"task:{task_id}")
            if not task_data:
                retries -= 1
                await asyncio.sleep(1)
                continue

            status = task_data.get("status", "unknown")
            total = int(task_data.get("total", 0))
            processed = int(task_data.get("processed", 0))
            message = task_data.get("message", "")

            payload = json.dumps(
                {
                    "event": "progress",
                    "status": status,
                    "progress": f"{(processed/total)*100:.1f}" if total > 0 else 0,
                    "processed": processed,
                    "total": total,
                    "message": message,
                }
            )
            yield f"{payload}"  # 保持SSE事件标准分隔符
            if status in ["completed", "failed"]:
                break

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
