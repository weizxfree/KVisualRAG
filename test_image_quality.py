import asyncio
import base64
import httpx
from PIL import Image
from io import BytesIO
import json
from litellm import acompletion

async def test_image_quality():
    # 图片URL
    image_url = "http://127.0.0.1:9110/ai-chat/tom1_2024年历史类本科批在辽宁招生计划(1)_6830569c7aa10aa5332c73d7.png"
    
    # 下载图片
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        image_data = response.content
        
        # 记录原始图片大小
        print(f"Original image size: {len(image_data)} bytes")
        
        # 转换为Base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        print(f"Base64 image size: {len(image_base64)} characters")
        
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "你是一个多模态AI助手，可以同时处理文本和图片信息。当用户提问时：重点关注图片中的关键信息：文字、图表、表格、数据等。分析要求：1. 仔细分析问题中提到的所有内容，结合图片内容信息进行回答，不要联想 2. 当不确定时，明确表示无法确定，并说明需要哪些额外信息"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    },
                    {
                        "type": "text",
                        "text": "北京航空航天大学招收专业"
                    }
                ]
            }
        ]

        # 测试在线版本 (OpenAI)
        # print("\n=== Testing Online Version (OpenAI) ===")
        # try:
        #     response = await acompletion(
        #         model="qwen-vl-plus",  # 使用 OpenAI 格式
        #         messages=messages,
        #         stream=True,
        #         api_base="https://dashscope.aliyuncs.com/api/v1",
        #         api_key="YOUR_API_KEY"  # 请替换为您的API密钥
        #     )
            
        #     print("\nModel Response:")
        #     async for chunk in response:
        #         if hasattr(chunk, 'choices') and chunk.choices:
        #             delta = chunk.choices[0].delta
        #             if hasattr(delta, 'content') and delta.content:
        #                 print(delta.content, end='', flush=True)
        # except Exception as e:
        #     print(f"Error in online version: {str(e)}")

        # 测试本地版本 (Ollama)
        print("\n=== Testing Local Version (Ollama) ===")
        try:
            response = await acompletion(
                model="ollama/qwen2.5vl:32b",  # 使用 Ollama 格式
                messages=messages,
                stream=True,
                api_base="http://localhost:11434",  # Ollama 默认地址
            )
            
            print("\nModel Response:")
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        print(delta.content, end='', flush=True)
        except Exception as e:
            print(f"Error in local version: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_image_quality()) 