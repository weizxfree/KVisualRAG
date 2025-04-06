import asyncio
import copy
import uuid
from app.db.milvus import milvus_client
from app.db.mongo import get_mongo
from app.rag.convert_file import convert_file_to_images, save_image_to_minio
from app.rag.get_embedding import get_embeddings_from_httpx
from app.db.miniodb import async_minio_manager
from app.core.logging import logger


def sort_and_filter(data, min_score=None, max_score=None):
    # 筛选
    if min_score is not None:
        data = [item for item in data if item["score"] >= min_score]
    if max_score is not None:
        data = [item for item in data if item["score"] <= max_score]
    # 排序
    sorted_data = sorted(data, key=lambda x: x["score"], reverse=True)
    return sorted_data


async def update_task_progress(redis, task_id, status, message):
    await redis.hset(f"task:{task_id}", mapping={"status": status, "message": message})


async def handle_processing_error(redis, task_id, error_msg):
    await redis.hset(
        f"task:{task_id}", mapping={"status": "failed", "message": error_msg}
    )


async def process_file(redis, task_id, username, knowledge_db_id, file_meta):
    try:
        # 从MinIO获取文件内容
        file_content = await async_minio_manager.get_file_from_minio(
            file_meta["minio_filename"]
        )

        # 解析为图片
        images_buffer = await convert_file_to_images(file_content)

        # 保存图片并生成嵌入
        image_ids = []
        for i, image_buffer in enumerate(images_buffer):
            # 保存图片到MinIO
            minio_imagename, image_url = await save_image_to_minio(
                username, file_meta["original_filename"], image_buffer
            )

            # 保存图片元数据
            image_id = f"{username}_{uuid.uuid4()}"
            db = await get_mongo()
            await db.add_images(
                file_id=file_meta["file_id"],
                images_id=image_id,
                minio_filename=minio_imagename,
                minio_url=image_url,
                page_number=i + 1,
            )
            image_ids.append(image_id)
        logger.info(
            f"task:{task_id}: save images of {file_meta['original_filename']} to minio and mongodb"
        )

        # 生成嵌入向量
        embeddings = await generate_embeddings(
            images_buffer, file_meta["original_filename"]
        )
        logger.info(
            f"task:{task_id}: {file_meta['original_filename']} generate_embeddings!"
        )

        # 插入Milvus
        collection_name = f"colqwen{knowledge_db_id.replace('-', '_')}"
        await insert_to_milvus(
            collection_name, embeddings, image_ids, file_meta["file_id"]
        )
        logger.info(
            f"task:{task_id}: images of {file_meta['original_filename']} insert to milvus {collection_name}!"
        )

        # 更新处理进度
        await redis.hincrby(f"task:{task_id}", "processed", 1)
        current = int(await redis.hget(f"task:{task_id}", "processed"))
        total = int(await redis.hget(f"task:{task_id}", "total"))
        logger.info(f"task:{task_id} files processed + 1!")

        if current == total:
            await redis.hset(f"task:{task_id}", "status", "completed")
            await redis.hset(
                f"task:{task_id}", "message", "All files processed successfully"
            )
            logger.info(f"task:{task_id} All files processed successfully")

    except Exception as e:
        await handle_processing_error(
            redis, task_id, f"File processing failed: {str(e)}"
        )
        raise


async def generate_embeddings(images_buffer, filename):
    # 将同步函数包装到线程池执行
    images_request = [
        ("images", (f"{filename}_{i}.png", img, "image/png"))
        for i, img in enumerate(images_buffer)
    ]
    return await get_embeddings_from_httpx(images_request, endpoint="embed_image")


async def insert_to_milvus(collection_name, embeddings, image_ids, file_id):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: [
            milvus_client.insert(
                {
                    "colqwen_vecs": emb,
                    "page_number": i,
                    "image_id": image_ids[i],
                    "file_id": file_id,
                },
                collection_name,
            )
            for i, emb in enumerate(embeddings)
        ],
    )


async def replace_image_content(messages):

    # 创建深拷贝以保证原始数据不变
    new_messages = copy.deepcopy(messages)
    # 遍历每条消息
    for message in new_messages:
        if "content" not in message:
            continue

        # 遍历content中的每个内容项
        for item in message["content"]:
            if isinstance(item, dict):
                # 检查类型是否为image_url
                if item.get("type") == "image_url":
                    image_base64 = (
                        await async_minio_manager.download_image_and_convert_to_base64(
                            item["image_url"]
                        )
                    )
                    item["image_url"] = {"url": f"data:image/png;base64,{image_base64}"}

    return new_messages
