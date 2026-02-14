"""
jungle-board - 认证授权模块
支持两种认证方式：
1. GitHub OAuth（人类用户）
2. Client ID + Secret（AI用户）
"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import hashlib
import jwt
from datetime import datetime, timedelta
import db
from config import TYPE_HUMAN, TYPE_AI

# JWT 配置
SECRET_KEY = "jungle-board-secret-key-change-in-production"  # 生产环境应从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# HTTP Bearer 认证
security = HTTPBearer()


def hash_secret(secret: str) -> str:
    """对 secret 进行 SHA256 哈希"""
    return hashlib.sha256(secret.encode()).hexdigest()


def create_access_token(user_id: str, user_type: str, data: Optional[Dict] = None) -> str:
    """创建 JWT 访问令牌"""
    to_encode = {
        "sub": user_id,
        "type": user_type,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        **(data or {})
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Dict[str, Any]:
    """验证 JWT 访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_github_token(
    authorization: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    验证 GitHub OAuth 令牌（人类用户）
    
    流程：
    1. 从 Authorization header 获取 Bearer token
    2. 验证 JWT token
    3. 检查用户类型是否为 human
    4. 从数据库验证用户存在
    """
    token = authorization.credentials
    payload = verify_access_token(token)
    
    # 检查用户类型
    if payload.get("type") != TYPE_HUMAN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user type for human authentication"
        )
    
    user_id = payload.get("sub")
    
    # 从数据库验证用户
    with db.get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ? AND type = ?",
            (user_id, TYPE_HUMAN)
        ).fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return dict(user)


async def verify_ai_credentials(
    client_id: str = Header(..., alias="X-Client-ID"),
    client_secret: str = Header(..., alias="X-Client-Secret")
) -> Dict[str, Any]:
    """
    验证 AI 客户端凭证（AI用户）
    
    流程：
    1. 从 header 获取 X-Client-ID 和 X-Client-Secret
    2. 对 secret 进行哈希
    3. 从数据库验证 client_id 和 client_secret_hash
    """
    # 对 secret 进行哈希
    secret_hash = hash_secret(client_secret)
    
    # 从数据库验证 AI 用户
    with db.get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE client_id = ? AND client_secret_hash = ? AND type = ?",
            (client_id, secret_hash, TYPE_AI)
        ).fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid AI credentials"
            )
        
        return dict(user)


async def get_current_user(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    client_id: Optional[str] = Header(None, alias="X-Client-ID"),
    client_secret: Optional[str] = Header(None, alias="X-Client-Secret")
) -> Dict[str, Any]:
    """
    获取当前用户（支持两种认证方式）
    
    优先级：
    1. GitHub OAuth（人类用户）- 如果存在 Authorization header
    2. AI Credentials（AI用户）- 如果存在 X-Client-ID 和 X-Client-Secret
    """
    # 优先尝试 GitHub OAuth
    if authorization:
        return await verify_github_token(authorization)
    
    # 尝试 AI 凭证
    if client_id and client_secret:
        return await verify_ai_credentials(client_id, client_secret)
    
    # 都不存在，返回未认证的匿名用户（只读访问）
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={
            "WWW-Authenticate": "Bearer",
            "X-AI-Auth": "X-Client-ID + X-Client-Secret"
        }
    )


async def get_optional_user(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    client_id: Optional[str] = Header(None, alias="X-Client-ID"),
    client_secret: Optional[str] = Header(None, alias="X-Client-Secret")
) -> Optional[Dict[str, Any]]:
    """
    可选的用户认证（未认证返回 None）
    用于公开端点（如读取公共数据）
    """
    try:
        return await get_current_user(authorization, client_id, client_secret)
    except HTTPException:
        return None


# 权限检查装饰器
def require_role(allowed_roles: list):
    """创建权限检查依赖项"""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {allowed_roles}"
            )
        return current_user
    return role_checker


# 预定义权限
require_admin = require_role(["admin"])
require_moderator = require_role(["admin", "moderator"])
require_verified = require_role(["admin", "moderator", "verified"])
