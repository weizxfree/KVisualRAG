from pydantic import BaseModel, ValidationError
from typing import Dict, Any
from fastapi import HTTPException


# 用于校验和解析请求体
def validate_json(schema: BaseModel, data: Dict[str, Any]) -> BaseModel:
    try:
        return schema(**data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
