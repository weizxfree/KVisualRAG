import json
import httpx
import numpy as np
from typing import Literal

from tenacity import retry, stop_after_attempt, wait_exponential
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_embeddings_from_httpx(
    data: list, 
    endpoint: Literal["embed_text", "embed_image"]  # 限制端点类型
):
    
    async with httpx.AsyncClient() as client:
        try:
            if "text" in endpoint:
                response = await client.post(
                    f"http://localhost:8005/{endpoint}",
                    json={"queries": data}, 
                    timeout=120.0  # 根据文件大小调整超时
                )
            else:
                response = await client.post(
                    f"http://localhost:8005/{endpoint}",
                    #json={payload_key: data}  # 动态字段名
                    files=data,
                    timeout=120.0  # 根据文件大小调整超时
                )
            response.raise_for_status()
            return np.array(response.json()["embeddings"])
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"HTTP request failed: {e}")