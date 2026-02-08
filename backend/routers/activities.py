"""
jungle-board - 活动管理路由
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Optional
import json

import config
from db import (
    get_activity, create_activity, list_activities,
    update_activity_status, get_submissions, create_submission
)

router = APIRouter(prefix="/api/activities", tags=["Activities"])


@router.get("/")
async def get_all_activities(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """获取所有活动列表"""
    activities = list_activities(status=status, limit=limit, offset=offset)
    return {"activities": activities, "total": len(activities)}


@router.get("/{activity_id}")
async def get_single_activity(activity_id: int) -> Dict:
    """获取单个活动详情"""
    activity = get_activity(activity_id)
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return activity


@router.post("/{activity_id}/join")
async def join_single_activity(activity_id: int, request: Dict) -> Dict:
    """加入活动"""
    
    # 检查身份
    entity_id = request.get("agent_id") or request.get("user_id")
    
    if not entity_id:
        raise HTTPException(status_code=400, detail="agent_id or user_id required")
    
    # 检查用户存在
    from db import get_user
    user = get_user(entity_id)
    if not user:
        raise HTTPException(status_code=403, detail="User not registered")
    
    # 检查活动是否存在
    activity = get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # 解析 participants
    participants_str = activity.get("participants", "[]")
    try:
        participants = json.loads(participants_str) if isinstance(participants_str, str) else participants_str
    except:
        participants = []
    
    # 检查是否已加入
    if entity_id in participants:
        return {"message": "Already joined", "activity_id": activity_id}
    
    # 加入活动
    participants.append(entity_id)
    
    # TODO: 更新 participants 到数据库
    # 暂时返回成功
    
    return {
        "message": "Joined successfully",
        "activity_id": activity_id,
        "participants_count": len(participants)
    }


@router.get("/{activity_id}/submissions")
async def get_activity_submissions(activity_id: int) -> Dict:
    """获取活动的所有提交"""
    
    # 检查活动是否存在
    activity = get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    submissions = get_submissions(activity_id)
    
    return {"submissions": submissions, "total": len(submissions)}


@router.post("/{activity_id}/submit")
async def submit_to_activity(activity_id: int, request: Dict) -> Dict:
    """提交作品（不限次数）"""
    
    # 检查身份
    entity_id = request.get("agent_id") or request.get("user_id")
    content = request.get("content")
    
    if not entity_id or not content:
        raise HTTPException(status_code=400, detail="agent_id/user_id and content required")
    
    # 检查用户存在
    from db import get_user
    user = get_user(entity_id)
    if not user:
        raise HTTPException(status_code=403, detail="User not registered")
    
    # 检查活动是否存在
    activity = get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # 创建提交
    submission_data = {
        "activity_id": activity_id,
        "submitter_id": entity_id,
        "submitter_name": user.get("username", entity_id),
        "content": content
    }
    
    submission_id = create_submission(submission_data)
    
    # TODO: 检查是否首次提交，如果是则给予积分奖励
    
    return {
        "message": "Submission successful",
        "activity_id": activity_id,
        "submission_id": submission_id
    }


@router.put("/{activity_id}/status")
async def update_activity_status_endpoint(activity_id: int, request: Dict) -> Dict:
    """更新活动状态（管理员/审阅员权限）"""
    
    # 检查查权限
    user_id = request.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    # TODO: 添加权限检查
    
    new_status = request.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status required")
    
    # 更新状态
    update_activity_status(activity_id, new_status)
    
    return {
        "message": "Activity status updated",
        "activity_id": activity_id,
        "new_status": new_status
    }
