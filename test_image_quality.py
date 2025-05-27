import asyncio
import base64
import httpx
from PIL import Image
from io import BytesIO
import json
from litellm import acompletion
import hashlib


async def test_image_quality():
    # 图片URL
    image_url = "http://127.0.0.1:9110/ai-chat/tom1_%E5%85%AC%E8%B7%AF%E6%A1%A5%E6%A2%81%E6%8A%97%E9%9C%87%E8%AE%BE%E8%AE%A1%E8%A7%84%E8%8C%83JTG%20T%202231%2001%202020_2020%E6%8A%97%E9%9C%87%E8%A7%84%E8%8C%83_68300594f3e6ee576d92003e.png?AWSAccessKeyId=miniouser&Signature=p8L%2BYG4M66HCjn0hGYnQhVlYUrw%3D&Expires=4901577620"
    
    # 下载图片
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        image_data = response.content
        
        # 记录原始图片大小
        print(f"Original image size: {len(image_data)} bytes")
        
        # 转换为Base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        direct_hash = hashlib.md5(image_base64.encode()).hexdigest()
        print(f"直接转换的base64 hashcode: {direct_hash}")

        print(f"Base64 image size: {len(image_base64)} characters")
        
        # 构建消息你是一个多模态ai助手，可以同时处理文本和图片信息。当用户提问时：重点关注图片中的关键信息：文字、图表、表格、数据等\n**分析要求**：\n1. 仔细分析问题中提到的所有内容，结合图片内容信息进行回答，不要联想\n2. 当不确定时，明确表示无法确定，并说明需要哪些额外信息\n\n需要保留公式
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "你是一个多模态ai助手，可以同时处理文本和图片信息。当用户提问时：重点关注图片中的关键信息：文字、图表、表格、数据等\n**分析要求**：\n1. 仔细分析问题中提到的所有内容，结合图片内容信息进行回答，不要联想\n2. 当不确定时，明确表示无法确定，并说明需要哪些额外信息\n\n需要保留公式"
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
                        "text": "桥梁抗震设防目标"
                    }
                ]
            }
        ]

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