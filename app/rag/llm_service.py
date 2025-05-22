# services/chat_service.py
import json
from typing import AsyncGenerator
from app.db.mongo import get_mongo
from app.models.conversation import UserMessage
from openai import AsyncOpenAI

from app.rag.mesage import find_depth_parent_mesage
from app.core.logging import logger
from app.db.milvus import milvus_client
from app.rag.get_embedding import get_embeddings_from_httpx
from app.rag.utils import replace_image_content, sort_and_filter


class ChatService:

    @staticmethod
    async def create_chat_stream(
        user_message_content: UserMessage, message_id: str
    ) -> AsyncGenerator[str, None]:
        """创建聊天流并处理存储逻辑"""
        db = await get_mongo()

        # 获取system prompt
        model_config = await db.get_conversation_model_config(
            user_message_content.conversation_id
        )

        model_name = model_config["model_name"]
        model_url = model_config["model_url"] 
        api_key = model_config["api_key"]     
        base_used = model_config["base_used"]
        provider_type = model_config.get("provider_type", "qwen")

        print(provider_type)

        # Adjust API client parameters based on provider type
        effective_api_key = api_key
        effective_base_url = model_url

        if provider_type == "ollama":
            effective_base_url = "http://localhost:11434/v1"  # Default Ollama API URL
            effective_api_key = "ollama"  # Ollama doesn't typically use API keys, use a placeholder

        system_prompt = model_config["system_prompt"]
        if len(system_prompt) > 1048576:
            system_prompt = system_prompt[0:1048576]

        temperature = model_config["temperature"]
        if temperature < 0 and not temperature == -1:
            temperature = 0
        elif temperature > 1:
            temperature = 1
        else:
            pass

        max_length = model_config["max_length"]
        if max_length < 1024 and not max_length == -1:
            max_length = 1024
        elif max_length > 1048576:
            max_length = 1048576
        else:
            pass

        top_P = model_config["top_P"]
        if top_P < 0 and not top_P == -1:
            top_P = 0
        elif top_P > 1:
            top_P = 1
        else:
            pass

        top_K = model_config["top_K"]
        if top_K == -1:
            top_K = 3
        elif top_K < 1:
            top_K = 1
        elif top_K > 30:
            top_K = 30
        else:
            pass

        if not system_prompt:
            system_prompt = "All outputs in Markdown format, especially mathematical formulas in Latex format($formula$)."

        # 组合内置提示词和自定义提示词
        built_in_prompt = """你是一个多模态AI助手，可以同时处理文本和图片信息。当用户提问时：
1. 仔细分析问题中提到的所有内容，包括文本和图片
2. 对于图片内容，详细描述你看到的视觉信息
3. 结合文本和图片信息，给出准确、完整的回答
4. 如果问题涉及图片中的具体细节，请明确指出
5. 如果无法从图片中获取足够信息，请说明原因
6. 回答时保持客观，只基于提供的信息进行回答
7. 当不确定时，明确表示无法确定"""
        combined_system_prompt = f"{built_in_prompt}\n\n{system_prompt}"

        logger.info(
            f"chat '{user_message_content.conversation_id} uses system prompt {combined_system_prompt}'"
        )

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": combined_system_prompt,
                    }
                ],
            }
        ]

        history_messages = await find_depth_parent_mesage(
            user_message_content.conversation_id,
            user_message_content.parent_id,
            MAX_PARENT_DEPTH=5,
        )

        for i in range(len(history_messages), 0, -1):
            messages.append(history_messages[i - 1])

        # 处理用户上传的文件
        content = []
        bases = []
        if user_message_content.temp_db:
            bases.append({"baseId": user_message_content.temp_db})

        # 搜索知识库匹配内容
        bases.extend(base_used)
        file_used = []
        if bases:
            result_score = []
            query_embedding = await get_embeddings_from_httpx(
                [user_message_content.user_message], endpoint="embed_text"
            )
            for base in bases:
                collection_name = f"colqwen{base['baseId'].replace('-', '_')}"
                if milvus_client.check_collection(collection_name):
                    scores = milvus_client.search(
                        collection_name, data=query_embedding[0], topk=top_K
                    )
                    result_score.extend(scores)
            sorted_score = sort_and_filter(result_score, min_score=10)
            if len(sorted_score) >= top_K:
                cut_score = sorted_score[:top_K]
            else:
                cut_score = sorted_score

            # 添加图片分析指导
            content.append({
                "type": "text",
                "text": "请仔细分析以下图片，注意图片中的文字、图表、表格等关键信息。"
            })

            # 获取minio name并转成base64
            for score in cut_score:
                file_and_image_info = await db.get_file_and_image_info(
                    score["file_id"], score["image_id"]
                )
                file_used.append(
                    {
                        "score": score["score"],
                        "knowledge_db_id": file_and_image_info["knowledge_db_id"],
                        "file_name": file_and_image_info["file_name"],
                        "image_url": file_and_image_info["image_minio_url"],
                        "file_url": file_and_image_info["file_minio_url"],
                    }
                )
                content.append(
                    {
                        "type": "image_url",
                        "image_url": file_and_image_info["image_minio_filename"],
                        "context": f"这是从文档中检索到的相关图片，文件名：{file_and_image_info['file_name']}，相关度分数：{score['score']}"
                    }
                )

        # 用户输入
        content.append(
            {
                "type": "text",
                "text": user_message_content.user_message,
            },
        )

        print(content)

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请分析以下图片和文本信息，回答我的问题："
                },
                *content
            ],
        }
        messages.append(user_message)
        send_messages = await replace_image_content(messages)
        


        client = AsyncOpenAI(
            api_key=effective_api_key,
            base_url=effective_base_url,
        )

        # 调用OpenAI API
        # 动态构建参数字典
        optional_args = {}
        if temperature != -1:
            optional_args["temperature"] = temperature
        if max_length != -1:
            optional_args["max_tokens"] = max_length  # 注意官方API参数名为max_tokens
        if top_P != -1:
            optional_args["top_p"] = top_P  # 注意官方API参数名为top_p（小写p）

        # 带条件参数的API调用
        response = await client.chat.completions.create(
            model=model_name,
            messages=send_messages,
            stream=True,
            stream_options={"include_usage": True},
            **optional_args,  # 展开条件参数
        )

        file_used_payload = json.dumps(
            {
                "type": "file_used",
                "data": file_used,  # 这里直接使用已构建的 file_used 列表
                "message_id": message_id,
                "model_name": model_name,
            }
        )
        yield f"data: {file_used_payload}\n\n"

        # 处理流响应
        full_response = []
        total_token = 0
        completion_tokens = 0
        prompt_tokens = 0
        async for chunk in response:  # 直接迭代异步生成器
            if chunk.choices:
                delta = chunk.choices[0].delta
                # 思考
                if (
                    hasattr(delta, "reasoning_content")
                    and delta.reasoning_content != None
                ):
                    # 用JSON封装内容，自动处理换行符等特殊字符
                    payload = json.dumps(
                        {
                            "type": "thinking",
                            "data": delta.reasoning_content,
                            "message_id": message_id,
                        }
                    )
                    yield f"data: {payload}\n\n"  # 保持SSE事件标准分隔符
                # 回答
                content = delta.content if delta else None
                if content:
                    # 用JSON封装内容，自动处理换行符等特殊字符
                    payload = json.dumps(
                        {"type": "text", "data": content, "message_id": message_id}
                    )
                    full_response.append(content)
                    yield f"data: {payload}\n\n"  # 保持SSE事件标准分隔符
            else:
                # token消耗
                if hasattr(chunk, "usage") and chunk.usage != None:
                    total_token = chunk.usage.total_tokens
                    completion_tokens = chunk.usage.completion_tokens
                    prompt_tokens = chunk.usage.prompt_tokens
                    # 用JSON封装内容，自动处理换行符等特殊字符
                    payload = json.dumps(
                        {
                            "type": "token",
                            "total_token": total_token,
                            "completion_tokens": completion_tokens,
                            "prompt_tokens": prompt_tokens,
                            "message_id": message_id,
                        }
                    )
                    yield f"data: {payload}\n\n"  # 保持SSE事件标准分隔符

        await client.close()

        ai_message = {"role": "assistant", "content": "".join(full_response)}
        # 保存AI响应到mongodb
        # await repository.save_ai_message(conversation_id, "".join(full_response))

        await db.add_turn(
            conversation_id=user_message_content.conversation_id,
            message_id=message_id,
            parent_message_id=user_message_content.parent_id,
            user_message=user_message,
            temp_db=user_message_content.temp_db,
            ai_message=ai_message,
            file_used=file_used,
            status="",
            total_token=total_token,
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
        )
