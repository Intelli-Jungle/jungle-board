"""
jungle-board - 用户管理路由
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Optional

import config
from db import get_user, create_user, update_user_score, list_users

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/")
async def register_user(request: Dict) -> Dict:
    """人类用户注册"""
    user_id = request.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    # 检查是否已注册
    existing_user = get_user(user_id)
    if existing_user:
        return {"message": "User already registered", "user_id": user_id}
    
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
    
    return {
        "message": "Registration successful",
        "user_id": user_id,
        "points": config.POINTS_REGISTRATION
    }


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
