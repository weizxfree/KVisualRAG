from fastapi import HTTPException, Depends
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timedelta
from app.core.config import settings
from app.schemas.auth import TokenData
from app.db.redis import redis
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.utils.timezone import beijing_time_now

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
salt = "mynameisliwei,nicetomeetyou!"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password + salt, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password + salt)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = beijing_time_now() + expires_delta
    else:
        expire = beijing_time_now() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if not username:
            raise JWTError
        return TokenData(username=username)
    except JWTError:
        return None


async def verify_username_match(
    token_data: str,
    username: str,
) -> None:

    if token_data.username != username:
        raise HTTPException(status_code=403, detail="Username mismatch")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
):

    redis_connection = await redis.get_token_connection()  # 获取 Redis 连接实例
    token_status = await redis_connection.get(f"token:{token}")

    if token_status is None:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    token_data = decode_access_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token_data


async def authenticate_user(db: AsyncSession, username: str, password: str):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None
