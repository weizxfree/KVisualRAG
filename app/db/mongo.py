from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DeleteMany, UpdateMany
from app.core.config import settings
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from app.db.ultils import parse_aggregate_result
from app.utils.timezone import beijing_time_now
from app.db.miniodb import async_minio_manager
from app.db.milvus import milvus_client
from pymongo.errors import DuplicateKeyError, BulkWriteError


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def _create_indexes(self):
        """创建所有必要的索引（唯一索引+普通索引）"""
        try:
            # 知识库集合索引
            await self.db.knowledge_bases.create_index(
                [("knowledge_base_id", 1)], unique=True, name="unique_kb_id"  # 唯一索引
            )
            await self.db.knowledge_bases.create_index(
                [("username", 1), ("is_delete", 1)],  # 复合普通索引
                name="user_kb_query",
            )

            # 模型配置索引
            await self.db.model_config.create_index(
                [("username", 1)],
                unique=True,
                name="unique_config_id",
            )

            # 文件集合索引
            await self.db.files.create_index(
                [("file_id", 1)], unique=True, name="unique_file_id"  # 唯一索引
            )
            await self.db.files.create_index(
                [("knowledge_db_id", 1)], name="kb_file_query"  # 普通索引
            )

            # 对话集合索引
            await self.db.conversations.create_index(
                [("conversation_id", 1)],
                unique=True,  # 唯一索引
                name="unique_conversation_id",
            )
            await self.db.conversations.create_index(
                [("username", 1), ("last_modify_at", -1)],  # 复合排序索引
                name="user_conversations",
            )

            logger.info("MongoDB 索引创建完成")
        except Exception as e:
            logger.error(f"索引创建失败: {str(e)}")
            raise

    async def connect(self):
        self.client = AsyncIOMotorClient(
            f"mongodb://{settings.mongodb_root_username}:{settings.mongodb_root_password}@{settings.mongodb_url}",
            maxPoolSize=settings.mongodb_pool_size,  # 设置最大连接池大小
            minPoolSize=settings.mongodb_min_pool_size,  # 设置最小连接池大小
        )
        self.db = self.client[settings.mongodb_db]
        # 添加索引优化（首次连接时执行）
        await self._create_indexes()

    async def close(self):
        if self.client:
            self.client.close()  # 使用 await 调用 close

    # config
    async def create_model_config(
        self,
        username: str,
        selected_model: str,
        model_id: str,
        model_name: str,
        model_url: str,
        api_key: str,
        base_used: list,
        system_prompt: str,
        temperature: float,
        max_length: int,
        top_P: float,
        top_K: int,
        provider_type: Optional[str] = "qwen",  # 新增 provider_type
    ):
        model_config = {
            "username": username,
            "selected_model": selected_model,
            "models": [
                self._build_model_dict(
                    model_id=model_id,
                    model_name=model_name,
                    model_url=model_url,
                    api_key=api_key,
                    base_used=base_used,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_length=max_length,
                    top_P=top_P,
                    top_K=top_K,
                    provider_type=provider_type,  # 传递 provider_type
                )
            ],
        }

        try:
            await self.db.model_config.insert_one(model_config)
            return {"status": "success", "username": username}
        except DuplicateKeyError:
            logger.error(f"username already exist: username: {username}")
            return {"status": "error", "message": "username already exist"}
        except Exception as e:
            logger.error(f"create config failed: {str(e)}")
            return {"status": "error", "message": f"mongo error: {str(e)}"}

    def _build_model_dict(
        self,
        model_id: str,
        model_name: str,
        model_url: str,
        api_key: str,
        base_used: list,
        system_prompt: str,
        temperature: float,
        max_length: int,
        top_P: float,
        top_K: int,
        provider_type: Optional[str] = "qwen",  # 新增 provider_type
    ) -> dict:
        return {
            "model_id": model_id,
            "model_name": model_name,
            "model_url": model_url,
            "api_key": api_key,
            "base_used": base_used,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_length": max_length,
            "top_P": top_P,
            "top_K": top_K,
            "provider_type": provider_type,  # 添加 provider_type
        }

    async def update_selected_model(self, username: str, model_id: str):
        """
        更新用户选定的模型 (selected_model 字段)
        同时验证目标 model_id 是否存在于该用户的 models 数组中
        """
        # 验证 model_id 是否存在
        model_exists = await self.db.model_config.find_one(
            {"username": username, "models.model_id": model_id}
        )

        if not model_exists:
            return {
                "status": "error",
                "message": f"Model ID {model_id} not found for user {username}",
            }

        # 更新 selected_model
        result = await self.db.model_config.update_one(
            {"username": username}, {"$set": {"selected_model": model_id}}
        )

        if result.matched_count == 0:
            return {"status": "error", "message": "User not found"}

        return {"status": "success", "username": username, "selected_model": model_id}

    async def add_model_config(
        self,
        username: str,
        model_id: str,
        model_name: str,
        model_url: str,
        api_key: str,
        base_used: list,
        system_prompt: str,
        temperature: float,
        max_length: int,
        top_P: float,
        top_K: int,
        provider_type: Optional[str] = "qwen",  # 新增 provider_type
    ):
        # 检查用户是否存在
        user_exists = await self.db.model_config.find_one({"username": username})
        if not user_exists:
            return {"status": "error", "message": "User not found"}

        # 检查 model_id 是否重复
        model_exists = await self.db.model_config.find_one(
            {"username": username, "models.model_id": model_id}
        )
        if model_exists:
            return {"status": "error", "message": "Model ID already exists"}

        # 构建新模型配置
        new_model = self._build_model_dict(
            model_id=model_id,
            model_name=model_name,
            model_url=model_url,
            api_key=api_key,
            base_used=base_used,
            system_prompt=system_prompt,
            temperature=temperature,
            max_length=max_length,
            top_P=top_P,
            top_K=top_K,
            provider_type=provider_type,  # 传递 provider_type
        )

        # 插入到数组
        result = await self.db.model_config.update_one(
            {"username": username}, {"$push": {"models": new_model}}
        )

        if result.modified_count == 1:
            return {"status": "success", "username": username, "model_id": model_id}
        else:
            return {"status": "error", "message": "Failed to add model"}

    async def delete_model_config(self, username: str, model_id: str):
        # 删除操作
        result = await self.db.model_config.update_one(
            {"username": username}, {"$pull": {"models": {"model_id": model_id}}}
        )

        # 处理结果
        if result.matched_count == 0:
            return {"status": "error", "message": "User not found"}
        elif result.modified_count == 0:
            return {"status": "error", "message": "Model ID not found"}
        else:
            return {"status": "success", "username": username, "model_id": model_id}

    async def update_model_config(
        self,
        username: str,
        model_id: str,
        model_name: Optional[str] = None,
        model_url: Optional[str] = None,
        api_key: Optional[str] = None,
        base_used: Optional[list] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_length: Optional[int] = None,
        top_P: Optional[float] = None,
        top_K: Optional[int] = None,
        provider_type: Optional[str] = None,  # 新增 provider_type
    ):
        # 构建更新字段
        update_fields = {}
        if model_name is not None:
            update_fields["models.$[elem].model_name"] = model_name
        if model_url is not None:
            update_fields["models.$[elem].model_url"] = model_url
        if api_key is not None:
            update_fields["models.$[elem].api_key"] = api_key
        if base_used is not None:
            update_fields["models.$[elem].base_used"] = base_used
        if system_prompt is not None:
            update_fields["models.$[elem].system_prompt"] = system_prompt
        if temperature is not None:
            update_fields["models.$[elem].temperature"] = temperature
        if max_length is not None:
            update_fields["models.$[elem].max_length"] = max_length
        if top_P is not None:
            update_fields["models.$[elem].top_P"] = top_P
        if top_K is not None:
            update_fields["models.$[elem].top_K"] = top_K
        if provider_type is not None:
            update_fields["models.$[elem].provider_type"] = provider_type

        # 执行更新
        try:
            result = await self.db.model_config.update_one(
                {"username": username},
                {"$set": update_fields},
                array_filters=[{"elem.model_id": model_id}],
            )
            if result.matched_count == 0:
                return {"status": "error", "message": "User not found"}
            elif result.modified_count == 0:
                return {"status": "success", "message": "No changes detected"}
            else:
                return {"status": "success", "username": username, "model_id": model_id}
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
        return {"status": "error", "message": str(e)}

    async def get_selected_model_config(self, username: str):
        # 获取用户配置
        user_config = await self.db.model_config.find_one({"username": username})
        if not user_config:
            return {"status": "error", "message": "User not found"}

        # 提取选中的 model_id
        selected_id = user_config.get("selected_model")
        if not selected_id:
            return {"status": "error", "message": "No selected model"}

        # 遍历 models 数组查找
        for model in user_config.get("models", []):
            if model.get("model_id") == selected_id:
                return {"status": "success", "select_model_config": model}

        return {"status": "error", "message": "Selected model not found"}

    async def get_all_models_config(self, username: str):
        # 直接返回 models 数组
        user_config = await self.db.model_config.find_one({"username": username})
        if not user_config:
            return {"status": "error", "message": "User not found"}
        return {
            "status": "success",
            "models": user_config.get("models", []),
            "selected_model": user_config.get("selected_model", ""),
        }

    # chat
    async def create_conversation(
        self,
        conversation_id: str,
        username: str,
        conversation_name: str,
        model_config: dict,
    ):
        """创建一个新的会话"""

        conversation = {
            "conversation_id": conversation_id,
            "conversation_name": conversation_name,
            "username": username,
            "model_config": model_config,
            "turns": [],  # 初始时为空列表，后续添加对话轮次
            "created_at": beijing_time_now(),
            "last_modify_at": beijing_time_now(),
            "is_read": False,
            "is_delete": False,
        }
        try:
            await self.db.conversations.insert_one(conversation)
            return {"status": "success", "id": conversation_id}
        except DuplicateKeyError:
            logger.warning(f"对话ID冲突: {conversation_id}")
            return {"status": "failed", "message": "对话ID已存在，请勿重复创建"}
        except Exception as e:
            logger.error(f"创建对话失败: {str(e)}")
            return {"status": "error", "message": f"数据库错误: {str(e)}"}

    async def get_conversation(self, conversation_id: str):
        """获取指定 conversation_id 的完整会话记录"""
        conversation = await self.db.conversations.find_one(
            {"conversation_id": conversation_id, "is_delete": False}
        )
        return conversation if conversation else None

    async def get_conversation_model_config(self, conversation_id: str):
        """获取指定 conversation_id 的system prompt"""
        conversation = await self.db.conversations.find_one(
            {"conversation_id": conversation_id, "is_delete": False}
        )
        return conversation["model_config"] if conversation else None

    async def get_conversations_by_user(self, username: str) -> List[Dict[str, Any]]:
        """按时间降序获取指定用户的所有会话"""
        cursor = self.db.conversations.find(
            {"username": username, "is_delete": False}
        ).sort(
            "last_modify_at", -1
        )  # -1 表示降序排列
        return await cursor.to_list(length=None)  # 返回所有匹配的记录

    async def update_conversation_name(
        self, conversation_id: str, new_name: str
    ) -> dict:
        result = await self.db.conversations.update_one(
            {"conversation_id": conversation_id, "is_delete": False},
            {
                "$set": {
                    "conversation_name": new_name,
                    "last_modify_at": beijing_time_now(),
                }
            },
        )
        if result.modified_count == 0:
            return {
                "status": "failed",
                "message": "Conversation not found or update failed",
            }
        return {"status": "success"}

    async def update_conversation_model_config(
        self, conversation_id: str, model_config: dict
    ) -> dict:
        result = await self.db.conversations.update_one(
            {"conversation_id": conversation_id, "is_delete": False},
            {
                "$set": {
                    "model_config": model_config,
                    "last_modify_at": beijing_time_now(),
                }
            },
        )
        if result.modified_count == 0:
            return {
                "status": "failed",
                "message": "Conversation not found or update failed",
            }
        return {"status": "success"}

    async def update_conversation_read_status(
        self, conversation_id: str, read_status=True
    ) -> dict:
        result = await self.db.conversations.update_one(
            {"conversation_id": conversation_id, "is_delete": False},
            {
                "$set": {
                    "is_read": read_status,
                }
            },
        )
        if result.modified_count == 0:
            return {
                "status": "failed",
                "message": "Conversation not found or update failed",
            }
        return {"status": "success"}

    async def add_turn(
        self,
        conversation_id: str,
        message_id: str,
        parent_message_id: str,
        user_message: str = "",
        ai_message: str = "",
        file_used: list = [],
        temp_db: str = "",
        status: str = "",
        total_token: int = 0,
        completion_tokens: int = 0,
        prompt_tokens: int = 0,
    ) -> Dict[str, Any]:
        """向指定的 conversation_id 中添加一轮对话"""
        turn = {
            "message_id": message_id,
            "parent_message_id": parent_message_id,
            "user_message": user_message,
            "temp_db": temp_db,
            "ai_message": ai_message,
            "file_used": file_used,
            "status": status,
            "timestamp": beijing_time_now(),
            "total_token": total_token,
            "completion_tokens": completion_tokens,
            "prompt_tokens": prompt_tokens,
        }
        result = await self.db.conversations.update_one(
            {"conversation_id": conversation_id, "is_delete": False},
            {
                "$push": {
                    "turns": turn,
                },
                "$set": {"last_modify_at": beijing_time_now()},
            },
        )
        return {"status": "success" if result.modified_count > 0 else "failed"}

    async def delete_conversation(self, conversation_id: str) -> dict:
        """根据 conversation_id 删除指定会话，并删除关联的临时知识库"""
        # 获取对话文档
        conversation = await self.db.conversations.find_one(
            {"conversation_id": conversation_id}
        )
        if not conversation:
            return {"status": "failed", "message": "Conversation not found"}

        # 收集所有关联的临时知识库ID
        temp_dbs = []
        for turn in conversation.get("turns", []):
            if temp_db := turn.get("temp_db"):
                if temp_db.strip():  # 过滤空值
                    temp_dbs.append(temp_db.strip())

        # 去重并删除临时知识库
        deletion_results = []
        for db_id in set(temp_dbs):
            result = await self.delete_knowledge_base(db_id)
            deletion_results.append({"knowledge_base_id": db_id, "result": result})
            milvus_client.delete_collection("colqwen" + db_id.replace("-", "_"))

        # 删除对话文档
        delete_result = await self.db.conversations.delete_one(
            {"conversation_id": conversation_id}
        )

        if delete_result.deleted_count == 1:
            return {
                "status": "success",
                "message": f"Conversation {conversation_id} deleted",
                "knowledge_base_deletion": deletion_results,
            }
        return {"status": "failed", "message": "Conversation not found"}

    async def delete_all_conversation(self, username: str) -> dict:
        """删除指定用户的所有会话及关联的临时知识库"""
        # 获取用户所有对话
        conversations = await self.db.conversations.find(
            {"username": username}
        ).to_list(length=None)

        # 收集所有临时知识库ID
        temp_dbs = []
        for conv in conversations:
            for turn in conv.get("turns", []):
                if temp_db := turn.get("temp_db"):
                    if temp_db.strip():
                        temp_dbs.append(temp_db.strip())

        # 去重并删除临时知识库
        deletion_results = []
        for db_id in set(temp_dbs):
            result = await self.delete_knowledge_base(db_id)
            deletion_results.append({"knowledge_base_id": db_id, "result": result})
            milvus_client.delete_collection("colqwen" + db_id.replace("-", "_"))

        # 删除所有对话文档
        delete_result = await self.db.conversations.delete_many({"username": username})

        if delete_result.deleted_count > 0:
            return {
                "status": "success",
                "deleted_count": delete_result.deleted_count,
                "knowledge_base_deletion": deletion_results,
            }
        return {"status": "failed", "message": "No conversations found"}

    # knowledge base
    async def create_knowledge_base(
        self,
        username: str,
        knowledge_base_name: str,
        knowledge_base_id: str,
        is_delete: bool,
    ):
        """创建一个新的知识库（如果 knowledge_base_id 不存在则创建，存在则跳过）"""
        # 检查是否已存在相同的 knowledge_base_id
        existing = await self.db.knowledge_bases.find_one(
            {"knowledge_base_id": knowledge_base_id}
        )
        if existing is not None:
            # 如果存在，直接返回，不执行插入
            return

        """创建知识库（使用唯一索引防止重复）"""
        knowledge_base = {
            "knowledge_base_id": knowledge_base_id,
            "knowledge_base_name": knowledge_base_name,
            "username": username,
            "files": [],
            "used_chat": [],
            "created_at": beijing_time_now(),
            "last_modify_at": beijing_time_now(),
            "is_delete": is_delete,
        }

        try:
            await self.db.knowledge_bases.insert_one(knowledge_base)
            return {"status": "success", "id": knowledge_base_id}
        except DuplicateKeyError:
            logger.warning(f"知识库ID冲突: {knowledge_base_id}")
            return {"status": "failed", "message": "知识库ID已存在，请勿重复创建"}
        except Exception as e:
            logger.error(f"创建知识库失败: {str(e)}")
            return {"status": "error", "message": f"数据库错误: {str(e)}"}

    async def get_knowledge_bases_by_user(self, username: str) -> List[Dict[str, Any]]:
        """按时间降序获取指定用户的所有会话"""
        cursor = self.db.knowledge_bases.find(
            {"username": username, "is_delete": False}
        ).sort(
            "last_modify_at", -1
        )  # -1 表示降序排列
        return await cursor.to_list(length=None)  # 返回所有匹配的记录

    async def delete_knowledge_base(self, knowledge_base_id: str) -> dict:
        """删除知识库及关联的所有文件"""
        # 查询知识库文档
        knowledge_base = await self.db.knowledge_bases.find_one(
            {"knowledge_base_id": knowledge_base_id}
        )
        if not knowledge_base:
            return {"status": "failed", "message": "知识库不存在"}

        # 收集所有关联文件ID（自动去重）
        file_ids = list({file["file_id"] for file in knowledge_base.get("files", [])})

        # 批量删除文件（包含MongoDB记录和MinIO文件）
        file_deletion_result = (
            await self.delete_files_bulk(file_ids)
            if file_ids
            else {"status": "success", "message": "无关联文件需要删除", "detail": {}}
        )

        # 删除知识库文档
        try:
            delete_result = await self.db.knowledge_bases.delete_one(
                {"knowledge_base_id": knowledge_base_id}
            )
        except Exception as e:
            logger.error(f"删除知识库失败 | ID: {knowledge_base_id} | 错误: {str(e)}")
            return {
                "status": "failed",
                "message": f"数据库删除失败: {str(e)}",
                "file_deletion": file_deletion_result,
            }

        # 处理结果
        response = {
            "status": "success",
            "message": "知识库及关联文件已删除",
            "detail": {
                "knowledge_base_deleted": delete_result.deleted_count,
                "file_deletion": file_deletion_result,
            },
        }

        # 处理部分成功情况
        if (
            file_deletion_result.get("status") != "success"
            or delete_result.deleted_count != 1
        ):
            response["status"] = "partial_success"
            error_messages = []

            if delete_result.deleted_count != 1:
                error_messages.append("知识库删除失败")

            if file_deletion_result.get("status") != "success":
                error_messages.append("部分文件删除失败")

            response["message"] = ",".join(error_messages)

        return response

    async def update_knowledge_base_name(
        self, knowledge_base_id: str, new_name: str
    ) -> dict:
        result = await self.db.knowledge_bases.update_one(
            {"knowledge_base_id": knowledge_base_id, "is_delete": False},
            {
                "$set": {
                    "knowledge_base_name": new_name,
                    "last_modify_at": beijing_time_now(),
                }
            },
        )
        if result.modified_count == 0:
            return {
                "status": "failed",
                "message": "Knowledge base not found or update failed",
            }
        return {"status": "success"}

    async def knowledge_base_add_file(
        self,
        knowledge_base_id: str,
        file_id: str,
        original_filename: str,
        minio_filename: str,
        minio_url: str,
    ) -> Dict[str, Any]:
        """向指定的 file_id 中添加解析的图片"""
        file = {
            "file_id": file_id,
            "filename": original_filename,
            "minio_filename": minio_filename,
            "minio_url": minio_url,
            "created_at": beijing_time_now(),
        }
        result = await self.db.knowledge_bases.update_one(
            {"knowledge_base_id": knowledge_base_id},
            {
                "$push": {
                    "files": file,
                },
                "$set": {"last_modify_at": beijing_time_now()},
            },
        )
        return {"status": "success" if result.modified_count > 0 else "failed"}

    async def get_files_by_knowledge_base_id(
        self, knowledge_base_id: str
    ) -> List[Dict[str, str]]:
        """
        通过知识库ID获取所有文件（仅返回url和filename）
        """
        try:
            # 查询未删除的知识库
            kb = await self.db.knowledge_bases.find_one(
                {
                    "knowledge_base_id": knowledge_base_id,
                },
                {"files": 1},  # 只返回files字段
            )

            if not kb or "files" not in kb:
                return []

            return [
                {"url": file.get("minio_url", ""), "filename": file.get("filename", "")}
                for file in kb["files"]
            ]

        except Exception as e:
            logger.error(
                f"获取知识库文件失败 | ID: {knowledge_base_id} | 错误: {str(e)}"
            )
            return []

    # files
    async def create_files(
        self,
        file_id: str,
        username: str,
        filename: str,
        minio_filename: str,
        minio_url: str,
        knowledge_db_id: str,
    ):
        """创建文件记录（带唯一索引保护）"""
        file = {
            "file_id": file_id,
            "filename": filename,
            "username": username,
            "minio_filename": minio_filename,
            "minio_url": minio_url,
            "knowledge_db_id": knowledge_db_id,
            "images": [],
            "created_at": beijing_time_now(),
            "last_modify_at": beijing_time_now(),
            "is_delete": False,
        }

        try:
            await self.db.files.insert_one(file)
            return {"status": "success"}
        except DuplicateKeyError:
            logger.warning(f"文件ID冲突: {file_id}")
            return {"status": "failed", "message": "文件ID已存在，请勿重复上传"}

    async def add_images(
        self,
        file_id: str,
        images_id: str,
        minio_filename: str,
        minio_url: str,
        page_number: str,
    ) -> Dict[str, Any]:
        """向指定的 file_id 中添加解析的图片"""
        images = {
            "images_id": images_id,
            "minio_filename": minio_filename,
            "minio_url": minio_url,
            "page_number": page_number,
        }
        result = await self.db.files.update_one(
            {"file_id": file_id, "is_delete": False},
            {
                "$push": {
                    "images": images,
                },
                "$set": {"last_modify_at": beijing_time_now()},
            },
        )
        return {"status": "success" if result.modified_count > 0 else "failed"}

    async def get_file_and_image_info(
        self, file_id: str, image_id: str
    ) -> Dict[str, Any]:
        """
        根据 file_id 和 image_id 获取：
        - knowledge_db_id
        - filename
        - 文件的 minio_filename 和 minio_url
        - 图片的 minio_filename 和 minio_url
        """
        # 查询文件文档，并匹配对应的图片
        file_doc = await self.db.files.find_one(
            {
                "file_id": file_id,
                "is_delete": False,
                "images.images_id": image_id,  # 确保存在该 image_id 的图片
            },
            projection={
                "knowledge_db_id": 1,
                "filename": 1,
                "minio_filename": 1,  # 文件的 minio_filename
                "minio_url": 1,  # 文件的 minio_url
                "images.$": 1,  # 使用 $ 操作符获取匹配的第一个图片元素
            },
        )

        if not file_doc:
            return {"status": "failed", "message": "file_id or image_id not found"}

        # 提取文件信息
        knowledge_db_id = file_doc.get("knowledge_db_id")
        file_name = file_doc.get("filename")
        file_minio_filename = file_doc.get("minio_filename")
        file_minio_url = file_doc.get("minio_url")  # 新增文件的 minio_url

        # 提取图片信息
        images = file_doc.get("images", [])
        if not images:
            return {"status": "failed", "message": "image not found"}

        image_info = images[0]  # 因为使用了 $ 操作符，数组只有一个匹配元素
        image_minio_filename = image_info.get("minio_filename")
        image_minio_url = image_info.get("minio_url")  # 新增图片的 minio_url

        # 返回所有字段
        return {
            "status": "success",
            "knowledge_db_id": knowledge_db_id,
            "file_name": file_name,
            "file_minio_filename": file_minio_filename,
            "file_minio_url": file_minio_url,  # 文件的 URL
            "image_minio_filename": image_minio_filename,
            "image_minio_url": image_minio_url,  # 图片的 URL
        }

    async def delete_files_base(self, file_id: str) -> dict:
        """根据 knowledge_base_id 删除指定会话"""
        result = await self.db.files.delete_one({"file_id": file_id})

        if result.deleted_count == 1:
            return {
                "status": "success",
                "message": f"Knowledge Base {file_id} deleted",
            }
        else:
            return {"status": "failed", "message": "Knowledge Base not found"}

    async def delete_files_bulk(self, file_ids: List[str]) -> dict:
        """批量删除文件记录及关联的 MinIO 文件"""
        # 去重处理
        unique_ids = list(set(file_ids))
        if not unique_ids:
            return {"status": "success", "message": "空文件列表，无需处理"}

        # 查询所有相关文档
        cursor = self.db.files.find({"file_id": {"$in": unique_ids}})
        files = await cursor.to_list(length=None)

        # 收集所有需要删除的 MinIO 文件
        minio_files = []
        found_ids = set()

        for file in files:
            found_ids.add(file["file_id"])
            # 主文件
            if main_file := file.get("minio_filename"):
                minio_files.append(main_file)
            # 图片文件
            minio_files.extend(
                img["minio_filename"]
                for img in file.get("images", [])
                if img.get("minio_filename")
            )

        # 执行 MinIO 批量删除
        error_messages = []

        try:
            if minio_files:
                await async_minio_manager.bulk_delete(list(set(minio_files)))  # 去重
                logger.info(f"批量删除 MinIO 文件成功")
        except Exception as e:
            error_messages.append(f"MinIO 批量删除异常: {str(e)}")
            logger.error(f"批量删除 MinIO 文件异常 | {str(e)}")

        # 执行 MongoDB 批量删除
        db_success = 0
        try:
            result = await self.db.files.bulk_write(
                [DeleteMany({"file_id": {"$in": unique_ids}})]
            )
            db_success = result.deleted_count
            logger.info(f"批量删除 mongo 数据库记录成功")
        except Exception as e:
            error_messages.append(f"数据库删除失败: {str(e)}")
            logger.error(f"批量删除数据库记录失败 | {str(e)}")

        # 处理未找到的 file_ids
        not_found_ids = list(set(unique_ids) - found_ids)

        # 构建响应
        response = {
            "status": "success",
            "message": f"成功删除 {db_success} 个文件记录",
            "detail": {
                "total_requested": len(unique_ids),
                "db_deleted": db_success,
                "minio_deleted": len(minio_files),
                "not_found_ids": not_found_ids,
                "errors": error_messages,
            },
        }

        if not_found_ids:
            response["message"] += f"，其中 {len(not_found_ids)} 个 ID 未找到"

        if error_messages:
            response["status"] = "partial_success"
            response["message"] += "（部分操作失败）"

        if db_success == 0 and len(not_found_ids) == len(unique_ids):
            response["status"] = "failed"
            response["message"] = "所有请求的文件 ID 均未找到"

        return response

    # 文件搜索
    async def get_kb_files_with_pagination(
        self,
        knowledge_base_id: str,
        keyword: str = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        获取知识库文件（带分页和搜索）
        """
        pipeline = [
            {"$match": {"knowledge_base_id": knowledge_base_id}},
            {"$unwind": "$files"},
        ]

        # 在展开数组后添加文件名过滤
        if keyword:
            pipeline.append(
                {"$match": {"files.filename": {"$regex": keyword, "$options": "i"}}}
            )

        pipeline.extend(
            [
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "file_id": "$files.file_id",
                            "filename": "$files.filename",
                            "url": "$files.minio_url",
                            "kb_id": "$knowledge_base_id",
                            "upload_time": "$files.created_at",
                            "kb_name": "$knowledge_base_name",
                        }
                    }
                },
                {
                    "$facet": {
                        "metadata": [{"$count": "total"}],
                        "data": [{"$skip": skip}, {"$limit": limit}],
                    }
                },
            ]
        )

        cursor = self.db.knowledge_bases.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return parse_aggregate_result(result)

    async def get_user_files_with_pagination(
        self, username: str, keyword: str = None, skip: int = 0, limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取用户所有文件（带分页和搜索）
        """
        pipeline = [
            {"$match": {"username": username, "is_delete": False}},
            {"$unwind": "$files"},  # 展开后每个文档的 files 字段变为对象（不是数组）
            # 关键字搜索（修正字段路径）
            (
                {"$match": {"files.filename": {"$regex": keyword, "$options": "i"}}}
                if keyword
                else {"$match": {}}
            ),
            # 重新映射字段（关键步骤）
            {
                "$replaceRoot": {
                    "newRoot": {
                        # 将 files 对象的字段提升到顶层
                        "file_id": "$files.file_id",
                        "filename": "$files.filename",
                        "url": "$files.minio_url",
                        # 假设 knowledge_base_id 是知识库的唯一标识
                        "kb_name": "$knowledge_base_name",
                        "kb_id": "$knowledge_base_id",
                        "upload_time": "$files.created_at",
                    }
                }
            },
            # 分页和统计
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [
                        {"$skip": skip},
                        {"$limit": limit},
                        # 不再需要 $project，因为字段已在 replaceRoot 中处理
                    ],
                }
            },
        ]

        cursor = self.db.knowledge_bases.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return parse_aggregate_result(result)

    async def delete_file_from_knowledge_base(
        self, knowledge_id: str, file_id: str
    ) -> dict:
        """
        从指定知识库中删除文件，并删除对应的文件记录和存储文件
        """
        # 检查文件是否存在于知识库中
        kb = await self.db.knowledge_bases.find_one(
            {"knowledge_base_id": knowledge_id, "files.file_id": file_id},
            projection={"files.$": 1},
        )
        if not kb:
            logger.warning(
                f"文件 {file_id} 不存在于知识库 {knowledge_id} 或知识库不存在"
            )
            return {"status": "failed", "message": "文件不存在于该知识库或知识库不存在"}

        # 从知识库的files数组中移除该文件
        update_result = await self.db.knowledge_bases.update_one(
            {"knowledge_base_id": knowledge_id},
            {"$pull": {"files": {"file_id": file_id}}},
        )
        if update_result.modified_count == 0:
            logger.error(f"从知识库 {knowledge_id} 中移除文件 {file_id} 失败")
            return {"status": "failed", "message": "文件移除失败"}

        # 检查文件记录是否属于该知识库
        file_doc = await self.db.files.find_one(
            {"file_id": file_id, "knowledge_db_id": knowledge_id}
        )
        if not file_doc:
            logger.warning(f"文件记录 {file_id} 不存在或不属于知识库 {knowledge_id}")
            return {"status": "failed", "message": "文件记录不存在或不属于该知识库"}

        # 删除文件记录及MinIO中的文件
        deletion_result = await self.delete_files_bulk([file_id])

        if deletion_result["status"] != "success":
            logger.error(f"删除文件 {file_id} 失败: {deletion_result}")
            return {
                "status": "partial_success",
                "message": "文件已从知识库中移除，但删除文件记录或存储文件失败",
                "detail": deletion_result,
            }

        logger.info(f"成功从知识库 {knowledge_id} 删除文件 {file_id}")
        return {"status": "success", "message": "文件删除成功"}

    async def bulk_delete_files_from_knowledge(
        self, delete_list: List[Dict[str, str]]
    ) -> dict:
        """
        批量从知识库删除文件（支持跨知识库）
        参数格式示例：[{"knowledge_id": "kb1", "file_id": "f1"}, ...]
        返回带详细操作结果的状态报告
        """
        # 去重处理并分组（按knowledge_id分组）
        unique_pairs = {(item["knowledge_id"], item["file_id"]) for item in delete_list}
        grouped = defaultdict(list)
        for kb_id, file_id in unique_pairs:
            grouped[kb_id].append(file_id)

        # 第一阶段：从各知识库批量移除文件引用
        bulk_operations = []
        for kb_id, file_ids in grouped.items():
            bulk_operations.append(
                UpdateMany(
                    {"knowledge_base_id": kb_id},
                    {"$pull": {"files": {"file_id": {"$in": file_ids}}}},
                    array_filters=[],  # 确保正确应用操作
                )
            )

        # 执行批量更新
        if bulk_operations:
            try:
                bulk_result = await self.db.knowledge_bases.bulk_write(bulk_operations)
                # MongoDB bulk_write不返回每个文档的状态，这里记录整体结果
                logger.info(f"批量更新影响知识库数量: {bulk_result.modified_count}")
            except BulkWriteError as e:
                logger.error(f"批量更新异常: {str(e)}")
                return {"status": "error", "message": "批量操作异常"}

        # 第二阶段：验证文件归属并收集待删除ID
        valid_files = []
        cursor = self.db.files.find(
            {
                "$or": [
                    {"knowledge_db_id": kb_id, "file_id": {"$in": file_ids}}
                    for kb_id, file_ids in grouped.items()
                ]
            },
            projection={"file_id": 1, "knowledge_db_id": 1},
        )

        async for doc in cursor:
            # 二次验证分组匹配
            if doc["file_id"] in grouped.get(doc["knowledge_db_id"], []):
                valid_files.append(doc["file_id"])

        # 第三阶段：执行文件删除
        deletion_result = await self.delete_files_bulk(valid_files)

        # 第四阶段：构建详细响应
        return {
            "status": (
                "success"
                if deletion_result["status"] == "success"
                else "partial_success"
            ),
            "detail": {
                "total_requested": len(unique_pairs),
                "valid_files_found": len(valid_files),
                "file_deletion": deletion_result,
                "knowledge_updates": {
                    "attempted": len(grouped),
                    "modified_count": (
                        bulk_result.modified_count if bulk_operations else 0
                    ),
                },
            },
        }


mongodb = MongoDB()


async def get_mongo():
    if mongodb.db is None:
        await mongodb.connect()
    return mongodb
