# app/rag/model_providers.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncGenerator, Optional
import json
from openai import AsyncOpenAI
import httpx
from app.core.logging import logger

class ModelProvider(ABC):
    """模型提供者的抽象基类，定义了所有模型提供者必须实现的接口"""
    
    @abstractmethod
    async def generate_stream(self, messages: List[Dict[str, Any]], model_name: str, 
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None,
                             top_p: Optional[float] = None,
                             **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """生成流式响应的抽象方法"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭客户端连接的抽象方法"""
        pass


class OpenAICompatibleProvider(ModelProvider):
    """兼容OpenAI API的模型提供者，如Qwen等"""
    
    def __init__(self, api_key: str, base_url: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    async def generate_stream(self, messages: List[Dict[str, Any]], model_name: str, 
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None,
                             top_p: Optional[float] = None,
                             **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """使用OpenAI兼容API生成流式响应"""
        optional_args = {}
        if temperature is not None:
            optional_args["temperature"] = temperature
        if max_tokens is not None:
            optional_args["max_tokens"] = max_tokens
        if top_p is not None:
            optional_args["top_p"] = top_p
            
        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            **optional_args
        )
        
        async for chunk in response:
            yield chunk
    
    async def close(self):
        """关闭OpenAI客户端连接"""
        await self.client.close()


class OllamaProvider(ModelProvider):
    """Ollama本地模型提供者"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)  # 设置较长的超时时间
    
    async def generate_stream(self, messages: List[Dict[str, Any]], model_name: str, 
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None,
                             top_p: Optional[float] = None,
                             **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """使用Ollama API生成流式响应"""
        # 转换消息格式为Ollama格式
        prompt = self._convert_messages_to_ollama_format(messages)
        
        # 构建请求参数
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
        }
        
        # 添加可选参数
        if temperature is not None:
            request_data["temperature"] = temperature
        if max_tokens is not None:
            request_data["num_predict"] = max_tokens
        if top_p is not None:
            request_data["top_p"] = top_p
            
        # 发送流式请求
        async with self.client.stream(
            "POST", f"{self.base_url}/api/generate", json=request_data
        ) as response:
            full_response = ""
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    # 模拟OpenAI格式的响应
                    if "response" in data:
                        content = data["response"]
                        full_response += content
                        
                        # 创建类似OpenAI的响应格式
                        chunk = type('OllamaChunk', (), {})
                        chunk.choices = [type('Choice', (), {})]
                        chunk.choices[0].delta = type('Delta', (), {})
                        chunk.choices[0].delta.content = content
                        
                        yield chunk
                        
                    # 处理完成事件
                    if data.get("done", False):
                        # 创建包含token使用信息的响应
                        chunk = type('OllamaChunk', (), {})
                        chunk.choices = []
                        
                        # 估算token使用量（Ollama不直接提供这些信息）
                        # 这里使用简单估算，实际应用中可能需要更准确的计算方法
                        prompt_tokens = len(prompt) // 4  # 粗略估计
                        completion_tokens = len(full_response) // 4  # 粗略估计
                        
                        chunk.usage = type('Usage', (), {})
                        chunk.usage.prompt_tokens = prompt_tokens
                        chunk.usage.completion_tokens = completion_tokens
                        chunk.usage.total_tokens = prompt_tokens + completion_tokens
                        
                        yield chunk
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Ollama response: {e}")
                except Exception as e:
                    logger.error(f"Error processing Ollama response: {e}")
    
    def _convert_messages_to_ollama_format(self, messages: List[Dict[str, Any]]) -> str:
        """将OpenAI格式的消息转换为Ollama格式的提示"""
        prompt = ""
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            # 处理内容为列表的情况（多模态内容）
            if isinstance(content, list):
                text_content = ""
                for item in content:
                    if item.get("type") == "text":
                        text_content += item.get("text", "")
                content = text_content
            
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        # 添加最后的助手提示
        if not prompt.endswith("Assistant: "):
            prompt += "Assistant: "
            
        return prompt
    
    async def close(self):
        """关闭httpx客户端连接"""
        await self.client.aclose()


def get_model_provider(provider_type: str, **kwargs) -> ModelProvider:
    """工厂函数，根据提供者类型创建相应的模型提供者实例"""
    if provider_type == "openai":
        return OpenAICompatibleProvider(
            api_key=kwargs.get("api_key", ""),
            base_url=kwargs.get("base_url", "")
        )
    elif provider_type == "ollama":
        return OllamaProvider(
            base_url=kwargs.get("base_url", "http://localhost:11434")
        )
    else:
        raise ValueError(f"不支持的模型提供者类型: {provider_type}")