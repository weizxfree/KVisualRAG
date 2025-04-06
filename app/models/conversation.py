# Pydantic 模型，用于输入数据验证
from typing import List
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    conversation_id: str
    username: str
    conversation_name: str
    chat_model_config: dict


class ConversationRenameInput(BaseModel):
    conversation_id: str
    conversation_new_name: str


class ConversationUpdateModelConfig(BaseModel):
    conversation_id: str
    chat_model_config: dict


class TurnInput(BaseModel):
    conversation_id: str
    message_id: str
    parent_message_id: str
    user_message: dict
    temp_db: str
    ai_message: dict
    file_used: list
    status: str
    total_token: int
    completion_tokens: int
    prompt_tokens: int


class TurnOutput(BaseModel):
    message_id: str
    parent_message_id: str
    user_message: dict
    temp_db: str
    ai_message: dict
    file_used: list
    user_file: list
    status: str
    timestamp: str
    total_token: int
    completion_tokens: int
    prompt_tokens: int


class ConversationOutput(BaseModel):
    conversation_id: str
    conversation_name: str
    username: str
    chat_model_config: dict
    turns: List[TurnOutput]
    created_at: str
    last_modify_at: str


class ConversationSummary(BaseModel):
    conversation_id: str
    created_at: str
    conversation_name: str
    chat_model_config: dict
    is_read: bool
    last_modify_at: str


class UserMessage(BaseModel):
    conversation_id: str
    parent_id: str
    user_message: str
    temp_db: str


class GetUserFiles(BaseModel):
    keyword: str
    page: int
    page_size: int
