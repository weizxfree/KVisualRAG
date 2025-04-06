from sqlalchemy import Column, Integer, String
from app.db.mysql_base import Base
import enum

from app.utils.timezone import beijing_time_now


class User(Base):
    __tablename__ = "users"

    """注册信息"""
    id = Column(Integer, primary_key=True, index=True)  # 用户ID，主键
    username = Column(
        String(50), unique=True, index=True, nullable=False
    )  # 用户名，唯一
    email = Column(String(100), unique=True, index=True, nullable=False)  # 邮箱，唯一
    hashed_password = Column(String(100), nullable=False)  # 哈希密码


    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
