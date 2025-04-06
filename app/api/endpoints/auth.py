import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from app.schemas.auth import TokenData, TokenSchema
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.db.mysql_session import get_mysql_session
from app.core.security import (
    decode_access_token,
    get_password_hash,
    create_access_token,
    authenticate_user,
    oauth2_scheme,
)
from app.db.redis import redis
from app.core.config import settings
from app.db.mongo import MongoDB, get_mongo

router = APIRouter()


@router.get("/verify-token", response_model=TokenData)
async def login_for_access_token(token: str = Depends(oauth2_scheme)):
    return decode_access_token(token)


@router.post("/login", response_model=TokenSchema)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_mysql_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )
    redis_connection = await redis.get_token_connection()  # 获取 Redis 连接实例
    await redis_connection.set(
        f"token:{access_token}",
        user.username,
        ex=int(access_token_expires.total_seconds()),
    )
    await redis_connection.set(
        f"user:{user.username}",
        access_token,
        ex=int(access_token_expires.total_seconds()),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": user.username, "email": user.email},
    }


@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_mysql_session),
    mongo: MongoDB = Depends(get_mongo),
):
    # Check if username or email already exists
    existing_user = await db.execute(select(User).where(User.username == user.username))
    if existing_user.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    existing_email = await db.execute(select(User).where(User.email == user.email))
    if existing_email.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    model_id=user.username + "_" + str(uuid.uuid4())
    await mongo.create_model_config(
        username=user.username,
        selected_model=model_id,
        model_id=model_id,
        model_name="qwen2.5-vl-32b-instruct",
        model_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-default-xxx",
        base_used=[],
        system_prompt="You are a helpful assistant.",
        temperature=-1,
        max_length=-1,
        top_P=-1,
        top_K=-1,
    )

    return UserResponse.model_validate(db_user)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    token_data = decode_access_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    redis_connection = await redis.get_token_connection()  # 获取 Redis 连接实例
    await redis_connection.delete(f"user:{token_data.username}")
    return {"message": "Logged out successfully"}
