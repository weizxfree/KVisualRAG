import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse, Response
from app.core.logging import logger
from typing import Awaitable, Callable

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        # 记录请求信息
        logger.info(f"Request: {request.method} {request.url} - Headers: {request.headers}")
        
        # 记录请求体（仅记录非流式请求）
        if request.method in ("POST", "PUT", "PATCH") and "text/event-stream" not in request.headers.get("Accept", ""):
            try:
                body = await request.json()
                logger.info(f"Request Body: {body}")
            except Exception as e:
                if not isinstance(e, json.JSONDecodeError):
                    logger.error(f"Error reading request body: {e}")

        # 获取原始响应
        response = await call_next(request)
        
        # 记录响应基本信息
        logger.info(f"Response status: {response.status_code} - Headers: {response.headers}")

        # 判断是否为流式响应
        is_streaming = isinstance(response, StreamingResponse) 
        is_sse = "text/event-stream" in response.media_type

        if is_streaming and is_sse:
            # 流式响应特殊处理
            async def logging_wrapper():
                full_body = []
                try:
                    async for chunk in response.body_iterator:
                        # 记录每个数据块（生产环境建议关闭）
                        logger.debug(f"Streaming chunk: {chunk.decode()}")
                        full_body.append(chunk)
                        yield chunk
                    # 流结束后记录完整响应（注意可能影响性能）
                    logger.info(f"Stream completed. Total length: {len(b''.join(full_body))} bytes")
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    raise

            return StreamingResponse(
                content=logging_wrapper(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        else:
            # 非流式响应处理
            response_body = []
            async for chunk in response.body_iterator:
                response_body.append(chunk)
            
            response_body_bytes = b"".join(response_body)
            
            # 重构响应体
            new_response = Response(
                content=response_body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

            # 记录响应体（排除二进制内容）
            content_type = new_response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    logger.info(f"Response Body: {response_body_bytes.decode()}")
                except Exception as e:
                    logger.error(f"JSON decode error: {e}")
            elif "text/" in content_type:
                logger.info(f"Response Text: {response_body_bytes.decode()}")
            elif not content_type.startswith("image/"):
                logger.info(f"Response Size: {len(response_body_bytes)} bytes")

            return new_response