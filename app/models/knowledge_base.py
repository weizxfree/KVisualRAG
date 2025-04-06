# Pydantic 模型，用于输入数据验证
from typing import Any, Dict, List
from pydantic import BaseModel


class KnowledgeBaseCreate(BaseModel):
    username: str
    knowledge_base_name: str

class KnowledgeBaseSummary(BaseModel):
    knowledge_base_id: str
    created_at: str
    knowledge_base_name: str
    last_modify_at: str
    file_number:int

class KnowledgeBaseRenameInput(BaseModel):
    knowledge_base_id: str
    knowledge_base_new_name: str

class PageResponse(BaseModel):
    data: list
    total: int
    page: int
    page_size: int
    total_pages: int

class BulkDeleteRequestItem(BaseModel):
    knowledge_id: str
    file_id: str