from io import BytesIO
import os
from fastapi import UploadFile
from pdf2image import convert_from_bytes
from app.db.miniodb import async_minio_manager
from bson.objectid import ObjectId
import time
from app.core.logging import logger

async def convert_file_to_images(file_content):
    # Read the contents of the uploaded file
    images = convert_from_bytes(file_content)
    images_buffer = []

    time_start = time.time()
    for i, image in enumerate(images):
        buffer = BytesIO()

        # 保存图像到内存缓冲区
        image.save(buffer, format="PNG", optimize=True)
    
        # 重置指针位置（关键步骤，参考MinIO上传逻辑）
        buffer.seek(0)
        images_buffer.append(buffer)
    spending_time = time.time() - time_start 
    logger.info(f"convert file to {len(images)} images spend time {spending_time}s")

    return images_buffer

async def save_file_to_minio(username:str, uploadfile: UploadFile):
    # 将生成的图像上传到 MinIO
    file_name = f"{username}_{os.path.splitext(uploadfile.filename)[0]}_{ObjectId()}{os.path.splitext(uploadfile.filename)[1]}"
    await async_minio_manager.upload_file(file_name, uploadfile)
    minio_url = await async_minio_manager.create_presigned_url(file_name)

    # minio_url = minio_url.replace("localhost:9110", "192.168.1.5:9110")
    # minio_url = minio_url.replace("localhost:9110", "127.0.0.1:9110")
    return file_name, minio_url

async def save_image_to_minio(username, filename, image_stream):
    # 将生成的图像上传到 MinIO
    file_name = f"{username}_{os.path.splitext(filename)[0]}_{ObjectId()}.png"
    await async_minio_manager.upload_image(file_name, image_stream)
    minio_url = await async_minio_manager.create_presigned_url(file_name)

    # minio_url = minio_url.replace("localhost:9110", "192.168.1.5:9110")
    # minio_url = minio_url.replace("localhost:9110", "127.0.0.1:9110")
    return file_name, minio_url
