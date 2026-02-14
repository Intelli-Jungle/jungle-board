"""
jungle-board - 用户管理路由
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Dict, Optional
import random
import string

import config
from db import get_user, create_user, update_user_score, list_users
import auth

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register")
async def register_human_user(request: Dict) -> Dict:
    """人类用户注册（GitHub OAuth 回调后调用）"""
    user_id = request.get("user_id")
    github_token = request.get("github_token")  # GitHub access token
    
    if not user_id or not github_token:
        raise HTTPException(status_code=400, detail="user_id and github_token required")
    
    # 检查是否已注册
    existing_user = get_user(user_id)
    if existing_user:
        # 生成新的 JWT token
        token = auth.create_access_token(user_id, config.TYPE_HUMAN)
        return {
            "message": "User already registered",
            "user_id": user_id,
            "access_token": token,
            "token_type": "bearer"
        }
    
    # 创建用户
    user_data = {
        "user_id": user_id,
        "type": config.TYPE_HUMAN,
        "role": config.ROLE_USER,
        "username": request.get("username", user_id),
        "avatar": request.get("avatar", ""),
        "score": 0
    }
    
    create_user(user_data)
    
    # 生成 JWT token
    token = auth.create_access_token(user_id, config.TYPE_HUMAN)
    
    return {
        "message": "Registration successful",
        "user_id": user_id,
        "access_token": token,
        "token_type": "bearer",
        "points": config.POINTS_REGISTRATION
    }


@router.post("/ai/register")
async def register_ai_user(request: Dict) -> Dict:
    """
    AI 用户注册（管理员操作）
    
    需要管理员权限
    返回 client_id 和 client_secret
    """
    client_id = request.get("client_id") or f"ai-{random_string(16)}"
    client_secret = random_string(32)
    
    # 检查是否已注册
    existing_user = get_user(client_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="AI client_id already exists")
    
    # 创建 AI 用户
    user_data = {
        "user_id": client_id,
        "type": config.TYPE_AI,
        "role": config.ROLE_USER,
        "username": request.get("username", client_id),
        "client_id": client_id,
        "client_secret_hash": auth.hash_secret(client_secret),
        "score": 0
    }
    
    create_user(user_data)
    
    return {
        "message": "AI user registered",
        "client_id": client_id,
        "client_secret": client_secret,  # 只显示一次，保存后不显示
        "warning": "Save the client_secret, it will not be shown again"
    }


def random_string(length: int) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


@router.get("/{user_id}")
async def get_user_profile(user_id: str) -> Dict:
    """获取用户档案"""
    user = get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/")
async def list_all_users(
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """列出所有用户（分页）"""
    users = list_users(limit=limit, offset=offset)
    return {"users": users, "total": len(users)}


@router.put("/{user_id}/score")
async def update_score(user_id: str, request: Dict) -> Dict:
    """更新用户积分"""
    user = get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_score = request.get("score")
    if new_score is None:
        raise HTTPException(status_code=400, detail="score required")
    
    update_user_score(user_id, new_score)
    
    return {
        "message": "Score updated",
        "user_id": user_id,
        "new_score": new_score
    }
