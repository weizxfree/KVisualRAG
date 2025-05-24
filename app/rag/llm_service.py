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

# LiteLLM 相关导入
try:
    from litellm import acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    acompletion = None


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

        print(f"Provider: {provider_type}, Model: {model_name}")

        # 统一使用 LiteLLM 处理所有模型
        if not LITELLM_AVAILABLE:
            raise Exception("LiteLLM is required but not available. Please install with: pip install litellm")
        
        print(f"🚀 Using unified LiteLLM architecture for all models")

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
        built_in_prompt = """你是一个多模态AI助手，可以同时处理文本和图片信息。当用户提问时：重点关注图片中的关键信息：文字、图表、表格、数据等
**分析要求**：
1. 仔细分析问题中提到的所有内容，结合图片内容信息进行回答，不要联想
2. 当不确定时，明确表示无法确定，并说明需要哪些额外信息"""
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

            # 获取minio name并转成URL，按分数排序
            for idx, score in enumerate(cut_score):
                file_and_image_info = await db.get_file_and_image_info(
                    score["file_id"], score["image_id"]
                )
                
                # 根据排名添加优先级标识
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
                    }
                )

                print(file_and_image_info["image_minio_url"]) 

        # 用户输入
        content.append(
            {
                "type": "text",
                "text": user_message_content.user_message,
            },
        )

        user_message = {
            "role": "user",
            "content": content
        }
        messages.append(user_message)
        send_messages = await replace_image_content(messages)
        
        # 发送 file_used 信息
        file_used_payload = json.dumps(
            {
                "type": "file_used",
                "data": file_used,  # 这里直接使用已构建的 file_used 列表
                "message_id": message_id,
                "model_name": model_name,
            }
        )
        yield f"data: {file_used_payload}\n\n"

        # 根据模型支持情况选择调用方式
        full_response = []
        total_token = 0
        completion_tokens = 0
        prompt_tokens = 0
        
        try:
            if LITELLM_AVAILABLE:
                print("🚀 Using LiteLLM for unified API call...")
                
                # 根据 provider_type 设置模型名称格式
                litellm_model = model_name
                if provider_type == "ollama":
                    litellm_model = f"ollama/{model_name}"
                else:
                    litellm_model = f"openai/{model_name}"
            
                # 构建 LiteLLM 参数
                litellm_params = {
                    "model": litellm_model,
                    "messages": send_messages,
                    "stream": True,
                }
                
                # 添加可选参数
                if temperature != -1:
                    litellm_params["temperature"] = temperature
                if max_length != -1:
                    litellm_params["max_tokens"] = max_length
                if top_P != -1:
                    litellm_params["top_p"] = top_P
                    
                litellm_params["stream_options"] = {"include_usage": True}
                # 设置 API 配置
                litellm_params["api_base"] = model_url
                litellm_params["api_key"] = api_key
                litellm_params["timeout"] = 60
                print(f"LiteLLM params: model={litellm_model}, messages={len(send_messages)}")
                print(f"Message content types: {[type(msg.get('content')) for msg in send_messages]}")

                response = await acompletion(**litellm_params)
                
                # 处理 LiteLLM 流响应
                async for chunk in response:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta

                        if (hasattr(delta, "reasoning_content") and delta.reasoning_content != None):
                            # 用JSON封装内容，自动处理换行符等特殊字符
                            payload = json.dumps(
                                {
                                    "type": "thinking",
                                    "data": delta.reasoning_content,
                                    "message_id": message_id,
                                }
                            )
                            yield f"data: {payload}\n\n"

                        if hasattr(delta, 'content') and delta.content:
                            content_chunk = delta.content
                            payload = json.dumps(
                                {"type": "text", "data": content_chunk, "message_id": message_id}
                            )
                            full_response.append(content_chunk)
                            yield f"data: {payload}\n\n"
                            
                    # 处理 token 统计
                    if hasattr(chunk, 'usage') and chunk.usage:
                        usage = chunk.usage
                        total_token = getattr(usage, 'total_tokens', 0)
                        completion_tokens = getattr(usage, 'completion_tokens', 0)
                        prompt_tokens = getattr(usage, 'prompt_tokens', 0)
                        
                        payload = json.dumps(
                            {
                                "type": "token",
                                "total_token": total_token,
                                "completion_tokens": completion_tokens,
                                "prompt_tokens": prompt_tokens,
                                "message_id": message_id,
                            }
                        )
                        yield f"data: {payload}\n\n"
                        
        except Exception as e:
            error_msg = f"API call error (LiteLLM): {str(e)}"
            print(f"Error: {error_msg}")
            print(f"Exception details: {type(e).__name__}: {str(e)}")
            
            yield f"data: {json.dumps({'type': 'error', 'data': error_msg})}\n\n"

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
