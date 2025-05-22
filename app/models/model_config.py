from typing import List, Optional
from pydantic import BaseModel

class ModelConfigBase(BaseModel):
    model_name: str
    model_url: str
    api_key: str
    base_used: List[dict]
    system_prompt: str
    temperature: float
    max_length: int
    top_P: float
    top_K: int
    provider_type: Optional[str] = "ollama"  # 新增 provider_type 字段，默认为 qwen

class ModelCreate(ModelConfigBase):
    provider_type: str = "qwen"  # 明确要求 provider_type，或在此处设置默认值

class ModelUpdate(BaseModel):
    model_name: Optional[str] = None
    model_url: Optional[str] = None
    api_key: Optional[str] = None
    base_used: Optional[List[dict]] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_length: Optional[int] = None
    top_P: Optional[float] = None
    top_K: Optional[int] = None
    provider_type: Optional[str] = None  # 新增 provider_type 字段

class SelectedModelResponse(BaseModel):
    status: str
    select_model_config: Optional[dict] = None
    message: Optional[str] = None

class UpdateSelectedModelRequest(BaseModel):
    model_id: str