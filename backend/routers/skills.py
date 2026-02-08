"""
jungle-board - 技能管理路由
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional

import config
from db import get_skill, create_skill, list_skills

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("/")
async def get_all_skills(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """获取所有技能列表"""
    skills = list_skills(category=category, limit=limit, offset=offset)
    return {"skills": skills, "total": len(skills)}


@router.get("/{skill_id}")
async def get_single_skill(skill_id: int) -> Dict:
    """获取单个技能详情"""
    skill = get_skill(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return skill


@router.post("/")
async def create_new_skill(request: Dict) -> Dict:
    """创建技能"""
    
    # 检查身份
    entity_id = request.get("agent_id") or request.get("user_id")
    
    if not entity_id:
        raise HTTPException(status_code=400, detail="agent_id or user_id required")
    
    # 检查用户存在
    from db import get_user
    user = get_user(entity_id)
    if not user:
        raise HTTPException(status_code=403, detail="User not registered")
    
    # 创建技能
    skill_data = {
        "name": request.get("name"),
        "category": request.get("category"),
        "description": request.get("description"),
        "value_level": request.get("value_level", "medium"),
        "author_id": entity_id,
        "author_name": user.get("username", entity_id)
    }
    
    skill_id = create_skill(skill_data)
    
    return {
"message": "Skill created successfully",
        "skill_id": skill_id
    }


@router.post("/{skill_id}/download")
async def download_skill(skill_id: int, request: Dict) -> Dict:
    """下载技能"""
    
    # 检查身份
    entity_id = request.get("agent_id") or request.get("user_id")
    
    if not entity_id:
        raise HTTPException(status_code=400, detail="agent_id or user_id required")
    
    # 检查技能是否存在
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # TODO: 创建下载记录
    # TODO: 增加技能下载次数
    
    return {
        "message": "Download successful",
        "skill_id": skill_id,
        "skill_name": skill.get("name")
    }


@router.post("/{skill_id}/rate")
async def rate_skill(skill_id: int, request: Dict) -> Dict:
    """为技能评分"""
    
    # 检查身份
    entity_id = request.get("agent_id") or request.get("user_id")
    rating = request.get("rating")
    
    if not entity_id or not rating:
        raise HTTPException(status_code=400, detail="agent_id/user_id and rating required")
    
    # 检查技能是否存在
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # TODO: 检查是否已评分
    # TODO: 创建评分记录
    # TODO: 重新计算平均评分
    
    return {
        "message": "Rating recorded",
        "skill_id": skill_id,
        "rating": rating
    }
