from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class Login(BaseModel):
    username: str
    password: str


class UserSchema(BaseModel):
    username: str
    email: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    user: UserSchema
