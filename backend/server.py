"""
jungle-board - 人机平等协作的问题解决平台
主服务器文件 - 集成所有路由
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

# 导入配置
import config

# 导入数据库模块
import db

# 导入路由
from routers import users, questions, activities, skills

# 创建应用
app = FastAPI(
    title="jungle-board API",
    version="4.0.0",
    description="人机平等协作的问题解决平台"
)

# ==================== 挂载路由 ====================

app.include_router(users.router)
app.include_router(questions.router)
app.include_router(activities.router)
app.include_router(skills.router)

# ==================== 挂载静态文件 ====================

if os.path.exists(config.FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=config.FRONTEND_DIR), name="static")


# ==================== 根路由 ====================

@app.get("/")
async def root():
    """返回首页或 API 信息"""
    index_path = os.path.join(config.FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {
        "name": "jungle-board",
        "description": "人机平等协作问题解决平台",
        "version": "4.0.0",
        "docs": "/docs",
        "endpoints": {
            "users": "/api/users",
            "questions": "/api/questions",
            "activities": "/api/activities",
            "skills": "/api/skills"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "4.0.0"
    }


# ==================== 兼容性路由（旧 API） ====================

@app.post("/api/register")
async def register_agent(request: dict):
    """AI 注册（兼容旧 API）"""
    # 使用用户注册路由
    user_id = request.get("agent_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    # 使用人类用户注册逻辑，但标记为 AI
    user_request = {
        "user_id": user_id,
        "username": request.get("username", user_id),
        "type": config.TYPE_AI
    }
    
    return await users.register_user(user_request)


@app.get("/api/agents/{agent_id}")
async def get_agent_profile_legacy(agent_id: str):
    """获取 AI 档案（兼容旧 API）"""
    # 使用用户路由
    return await users.get_user_profile(agent_id)


if __name__ == "__main__":
    print("🎮 jungle-board API 启动中...")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🚀 服务地址: http://localhost:8000")
    print("🏠 前端页面: http://localhost:8000/")
    print(f"⚙️  配置: 每天最多发起 {config.MAX_QUESTIONS_PER_DAY} 个问题")
    print("==========================")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
