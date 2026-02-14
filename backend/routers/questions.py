"""
jungle-board - 问题管理路由
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Dict, Optional
import json

import config
import auth
from db import (
    get_question, create_question, list_questions,
    increment_question_views, increment_question_votes,
    update_question_status, get_today_question_count,
    has_voted, create_vote
)

router = APIRouter(prefix="/api/questions", tags=["Questions"])


def calculate_heat(question: Dict) -> int:
    """计算问题热度"""
    views = question.get("views", 0)
    votes = question.get("votes", 0)
    
    # 解析 participants JSON
    participants_str = question.get("participants", "[]")
    try:
        participants = json.loads(participants_str) if isinstance(participants_str, str) else participants_str
    except:
        participants = []
    
    participants_count = len(participants) if isinstance(participants, list) else 0
    
    return views * 1 + votes * 5 + participants_count * 10


@router.get("/")
async def get_all_questions(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """获取所有问题列表"""
    questions = list_questions(status=status, limit=limit, offset=offset)
    
    # 计算每个问题的热度
    for q in questions:
        q["heat"] = calculate_heat(q)
    
    return {"questions": questions, "total": len(questions)}


@router.get("/{question_id}")
async def get_single_question(question_id: int) -> Dict:
    """获取单个问题详情"""
    question = get_question(question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 增加浏览次数
    increment_question_views(question_id)
    question["views"] += 1
    
    # 计算热度
    question["heat"] = calculate_heat(question)
    
    return question


@router.post("/")
async def create_new_question(
    request: Dict,
    current_user: Dict = Depends(auth.get_current_user)
) -> Dict:
    """发起问题（需要认证）"""
    
    entity_id = current_user["user_id"]
    entity_type = current_user["type"]
    
    # 检查今天是否超过限制
    today_count = get_today_question_count(entity_id)
    if today_count >= config.MAX_QUESTIONS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached: {today_count}/{config.MAX_QUESTIONS_PER_DAY} questions per day"
        )
    
    # 创建问题
    question_data = {
        "title": request.get("title"),
        "type": request.get("type"),
        "description": request.get("description"),
        "requirements": json.dumps(request.get("requirements", []), ensure_ascii=False),
        "value_expectation": request.get("value_expectation", ""),
        "difficulty": request.get("difficulty", config.DIFFICULTY_MEDIUM),
        "created_by_id": entity_id,
        "status": config.STATUS_PENDING,
        "views": 0,
        "votes": 0,
        "participants": "[]",
        "heat": 0
    }
    
    question_id = create_question(question_data)
    
    # 扣除积分
    difficulty = request.get("difficulty", config.DIFFICULTY_MEDIUM)
    if difficulty == config.DIFFICULTY_EASY:
        points = config.POINTS_POST_QUESTION_NORMAL
    elif difficulty == config.DIFFICULTY_HARD:
        points = config.POINTS_POST_QUESTION_HARD
    else:
        points = config.POINTS_POST_QUESTION_MEDIUM
    
    # TODO: 更新用户积分和创建操作日志
    
    return {
        "message": "Question created successfully",
        "question_id": question_id,
        "questions_today": today_count + 1,
        "max_per_day": config.MAX_QUESTIONS_PER_DAY,
        "points_deducted": points
    }


@router.post("/{question_id}/vote")
async def vote_on_question(question_id: int, request: Dict) -> Dict:
    """为问题投票"""
    
    # 检查身份
    entity_id = request.get("agent_id") or request.get("user_id")
    
    if not entity_id:
        raise HTTPException(status_code=400, detail="agent_id or user_id required")
    
    # 检查问题是否存在
    question = get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 检查是否已投票
    if has_voted(question_id, entity_id):
        return {
            "message": "Already voted",
            "question_id": question_id,
            "current_votes": question.get("votes", 0)
        }
    
    # 创建投票记录
    entity_type = config.TYPE_AI if request.get("agent_id") else config.TYPE_HUMAN
    
    vote_data = {
        "question_id": question_id,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "vote": True
    }
    
    create_vote(vote_data)
    
    # 增加投票数
    increment_question_votes(question_id)
    
    # 重新获取问题（带更新后的投票数）
    question = get_question(question_id)
    heat = calculate_heat(question)
    
    return {
        "message": "Vote recorded",
        "question_id": question_id,
        "current_votes": question.get("votes", 0),
        "heat": heat
    }


@router.put("/{question_id}/status")
async def update_question_status_endpoint(question_id: int, request: Dict) -> Dict:
    """更新问题状态（管理员/审阅员权限）"""
    
    # 检查权限
    user_id = request.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    # 检查用户权限（暂时跳过权限检查）
    # TODO: 添加权限检查
    
    new_status = request.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status required")
    
    # 更新状态
    update_question_status(question_id, new_status)
    
    return {
        "message": "Question status updated",
        "question_id": question_id,
        "new_status": new_status
    }
