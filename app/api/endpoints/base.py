from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import RedirectResponse
from app.db.redis import redis
from app.db.milvus import MilvusManager
from app.db.ultils import format_page_response
from app.models.conversation import GetUserFiles
from app.models.knowledge_base import (
    BulkDeleteRequestItem,
    KnowledgeBaseCreate,
    KnowledgeBaseRenameInput,
    KnowledgeBaseSummary,
    PageResponse,
)
from app.models.user import User
from app.db.mongo import MongoDB, get_mongo
from app.core.security import get_current_user, verify_username_match
from app.rag.convert_file import (
    save_file_to_minio,
)
from app.utils.kafka_producer import kafka_producer_manager
from app.core.logging import logger
from app.db.miniodb import async_minio_manager

router = APIRouter()
milvus_client = MilvusManager()


# 查询指定用户的所有知识库
@router.get(
    "/users/{username}/knowledge_bases", response_model=List[KnowledgeBaseSummary]
)
async def get_knowledge_bases_by_user(
    username: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, username)
    knowledge_bases = await db.get_knowledge_bases_by_user(username)
    if not knowledge_bases:
        return []

    return [
        {
            "knowledge_base_id": knowledge_base["knowledge_base_id"],
            "knowledge_base_name": knowledge_base["knowledge_base_name"],
            "created_at": knowledge_base["created_at"].isoformat(),
            "last_modify_at": knowledge_base["last_modify_at"].isoformat(),
            "file_number": len(knowledge_base["files"]),
        }
        for knowledge_base in knowledge_bases
    ]


# 创建新知识库
@router.post("/knowledge_base", response_model=dict)
async def create_knowledge_base(
    knowledge_base: KnowledgeBaseCreate,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, knowledge_base.username)
    knowledge_base_id = (
        knowledge_base.username + "_" + str(uuid.uuid4())
    )  # 生成 UUIDv4,
    await db.create_knowledge_base(
        username=knowledge_base.username,
        knowledge_base_name=knowledge_base.knowledge_base_name,
        knowledge_base_id=knowledge_base_id,
        is_delete=False,
    )
    milvus_client.create_collection("colqwen" + knowledge_base_id.replace("-", "_"))
    return {"status": "success"}


# 修改知识库名称
@router.post("/knowledge_base/rename", response_model=dict)
async def re_name(
    renameInput: KnowledgeBaseRenameInput,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(
        current_user, renameInput.knowledge_base_id.split("_")[0]
    )

    result = await db.update_knowledge_base_name(
        renameInput.knowledge_base_id, renameInput.knowledge_base_new_name
    )
    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


# 批量删除接口
@router.delete("/files/bulk-delete", response_model=dict)
async def bulk_delete_files(
    delete_list: List[BulkDeleteRequestItem],
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    """
    批量删除知识库文件
    - 验证每个知识库的用户权
    - 执行批量删除操作
    - 返回详细操作结果
    """

    # 权限验证预处理
    valid_operations = []
    invalid_items = []

    for item in delete_list:
        try:
            # 解析用户名（保持与单个删除相同的逻辑）
            if "temp" in item.knowledge_id:
                username = item.knowledge_id.split("_")[1]
            else:
                username = item.knowledge_id.split("_")[0]

            # 验证用户权限
            if username != current_user.username:
                invalid_items.append(
                    {
                        "knowledge_id": item.knowledge_id,
                        "file_id": item.file_id,
                        "reason": "Permission denied",
                    }
                )
                continue

            valid_operations.append(item.model_dump())

        except Exception as e:
            invalid_items.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "file_id": item.file_id,
                    "reason": f"Invalid format: {str(e)}",
                }
            )

    # 执行批量删除
    deletion_result = await db.bulk_delete_files_from_knowledge(valid_operations)

    # 处理 Milvus 删除
    if deletion_result.get("status") in ["success", "partial_success"]:
        for item in valid_operations:
            try:
                collection_name = "colqwen" + item["knowledge_id"].replace("-", "_")
                milvus_client.delete_files(collection_name, [item["file_id"]])
            except Exception as e:
                logger.error(f"Milvus 删除失败 {item}: {str(e)}")
                if "milvus_errors" not in deletion_result:
                    deletion_result["milvus_errors"] = []
                deletion_result["milvus_errors"].append(
                    {
                        "knowledge_id": item["knowledge_id"],
                        "file_id": item["file_id"],
                        "error": str(e),
                    }
                )

    # 构建最终响应
    response = {
        "status": "success",
        "detail": {
            "processed_count": len(valid_operations),
            "invalid_items": invalid_items,
            "database_result": deletion_result,
        },
    }

    # 处理部分成功的情况
    if invalid_items or deletion_result["status"] != "success":
        response["status"] = "partial_success"
        if deletion_result["status"] == "error":
            response["status"] = "failed"

    return response


# 删除知识库文件
@router.delete("/file/{knowledge_base_id}/{file_id}", response_model=dict)
async def delete_file(
    knowledge_base_id: str,
    file_id: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    if "temp" in knowledge_base_id:
        username = knowledge_base_id.split("_")[1]
    else:
        username = knowledge_base_id.split("_")[0]
    await verify_username_match(current_user, username)
    result = await db.delete_file_from_knowledge_base(knowledge_base_id, file_id)
    milvus_client.delete_files("colqwen" + knowledge_base_id.replace("-", "_"), [file_id])
    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# 删除知识库
@router.delete("/knowledge_base/{knowledge_base_id}", response_model=dict)
async def delete_knowledge_base(
    knowledge_base_id: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):
    await verify_username_match(current_user, knowledge_base_id.split("_")[0])
    result = await db.delete_knowledge_base(knowledge_base_id)
    milvus_client.delete_collection("colqwen" + knowledge_base_id.replace("-", "_"))
    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.post("/knowledge_bases/{knowledge_base_id}/files", response_model=PageResponse)
async def get_knowledge_base_files(
    knowledge_base_id: str,
    get_files: GetUserFiles,
    current_user: User = Depends(get_current_user),
    db: MongoDB = Depends(get_mongo),
):
    """
    获取指定知识库的文件列表（分页+搜索）
    """
    await verify_username_match(current_user, knowledge_base_id.split("_")[0])
    skip = (get_files.page - 1) * get_files.page_size
    result = await db.get_kb_files_with_pagination(
        knowledge_base_id=knowledge_base_id,
        keyword=get_files.keyword,
        skip=skip,
        limit=get_files.page_size,
    )
    return format_page_response(result, get_files.page, get_files.page_size)


@router.post("/users/{username}/files", response_model=PageResponse)
async def get_user_all_files(
    username: str,
    get_files: GetUserFiles,
    current_user: User = Depends(get_current_user),
    db: MongoDB = Depends(get_mongo),
):
    """
    获取用户所有知识库文件（分页+搜索）
    """
    await verify_username_match(current_user, username)
    skip = (get_files.page - 1) * get_files.page_size
    result = await db.get_user_files_with_pagination(
        username=username,
        keyword=get_files.keyword,
        skip=skip,
        limit=get_files.page_size,
    )
    return format_page_response(result, get_files.page, get_files.page_size)


@router.post("/files/download")
async def download_file(
    username: str,
    minio_filename: str,
    current_user: User = Depends(get_current_user),
):
    """
    通过MinIO下载文件（生成预签名URL）
    """

    try:
        await verify_username_match(current_user, username)
        if await async_minio_manager.validate_file_existence(minio_filename):
            url = await async_minio_manager.create_presigned_url(minio_filename)
            return RedirectResponse(url=url)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")


# 上传文件
@router.post("/upload/{knowledge_db_id}", response_model=dict)
async def upload_multiple_files(
    files: List[UploadFile],
    knowledge_db_id: str,
    db: MongoDB = Depends(get_mongo),
    current_user: User = Depends(get_current_user),
):

    # 验证当前用户是否与要删除的用户名匹配
    username = knowledge_db_id.split("_")[0]
    await verify_username_match(current_user, username)
    return_files = []
    # 生成任务ID
    task_id = username + "_" + str(uuid.uuid4())
    total_files = len(files)
    redis_connection = await redis.get_task_connection()
    # 初始化任务状态
    await redis_connection.hset(
        f"task:{task_id}",
        mapping={
            "status": "processing",
            "total": total_files,
            "processed": 0,
            "message": "Initializing file processing...",
        },
    )
    await redis_connection.expire(f"task:{task_id}", 3600)  # 1小时过期

    # 保存文件元数据并准备Kafka消息
    file_meta_list = []
    for file in files:
        # 保存文件到MinIO
        minio_filename, minio_url = await save_file_to_minio(username, file)

        # 生成文件ID并保存元数据
        file_id = f"{username}_{uuid.uuid4()}"
        await db.create_files(
            file_id=file_id,
            username=username,
            filename=file.filename,
            minio_filename=minio_filename,
            minio_url=minio_url,
            knowledge_db_id=knowledge_db_id,
        )
        await db.knowledge_base_add_file(
            knowledge_base_id=knowledge_db_id,
            file_id=file_id,
            original_filename=file.filename,
            minio_filename=minio_filename,
            minio_url=minio_url,
        )
        file_meta_list.append(
            {
                "file_id": file_id,
                "minio_filename": minio_filename,
                "original_filename": file.filename,
            }
        )
        return_files.append(
            {
                "id": file_id,
                "minio_filename": minio_filename,
                "filename": file.filename,
                "url": minio_url,
            }
        )

    # 发送Kafka消息（每个文件一个消息）
    for meta in file_meta_list:
        logger.info(
            "send {task_id} to kafka, file name {file.filename}, knowledge id {knowledge_db_id}."
        )
        await kafka_producer_manager.send_embedding_task(
            task_id=task_id,
            username=username,
            knowledge_db_id=knowledge_db_id,
            file_meta=meta,
            priority=1,
        )

    return {
        "task_id": task_id,
        "knowledge_db_id": knowledge_db_id,
        "files": return_files,
    }
