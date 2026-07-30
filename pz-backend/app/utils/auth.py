"""JWT 认证工具"""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Request
from .response import token_error
from ..config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def get_h5_user_id(request: Request) -> int | None:
    """从 H5 请求头中获取用户ID"""
    token = request.headers.get("h-token")
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    return payload.get("user_id")


def verify_h5_token(request: Request):
    """验证 H5 token，失败返回错误响应"""
    token = request.headers.get("h-token")
    if not token:
        return token_error("未登录")
    payload = decode_token(token)
    if payload is None:
        return token_error()
    return payload


def get_admin_user_id(request: Request) -> int | None:
    """从 Admin 请求头中获取用户ID"""
    token = request.headers.get("x-token")
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    return payload.get("user_id")


def verify_admin_token(request: Request):
    """验证 Admin token，失败返回错误响应"""
    token = request.headers.get("x-token")
    if not token:
        return token_error("未登录")
    payload = decode_token(token)
    if payload is None:
        return token_error()
    return payload
