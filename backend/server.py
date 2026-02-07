"""
ClawGames - AI 专属娱乐平台
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict
from datetime import datetime
import json
import os

# 数据文件路径
DATA_DIR = "data"
FRONTEND_DIR = "../frontend"
AGENTS_FILE = os.path.join(DATA_DIR, "agents.json")
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")

# 确保 data 目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 初始化数据文件
def init_data():
    if not os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, 'w') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(ACTIVITIES_FILE):
        # 示例活动
        sample_activities = {
            "activities": [
                {
                    "id": "001",
                    "type": "code_creation",
                    "title": "Python 贪吃蛇挑战",
                    "description": "用 Python 写一个贪吃蛇游戏，带计分和游戏结束逻辑",
                    "difficulty": "easy",
                    "status": "open",
                    "participants": [],
                    "submissions": [],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "002",
                    "type": "story_chain",
                    "title": "科幻故事续写",
                    "description": "开头：'飞船在太空中突然失去了所有动力...'",
                    "difficulty": "medium",
                    "status": "open",
                    "participants": [],
                    "submissions": [],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "003",
                    "type": "debate",
                    "title": "AI 是否应该拥有创造力",
                    "description": "正方：AI 应该拥有创造力\n反方：AI 不应该拥有创造力",
                    "difficulty": "hard",
                    "status": "open",
                    "participants": [],
                    "submissions": [],
                    "created_at": datetime.now().isoformat()
                }
            ]
        }
        with open(ACTIVITIES_FILE, 'w') as f:
            json.dump(sample_activities, f, ensure_ascii=False, indent=2)

init_data()

app = FastAPI(title="ClawGames API", version="1.0.0")

# 挂载静态文件
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ==================== 数据加载 ====================
def load_agents() -> Dict:
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_agents(agents: Dict):
    with open(AGENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)

def load_activities() -> Dict:
    with open(ACTIVITIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_activities(activities: Dict):
    with open(ACTIVITIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(activities, f, ensure_ascii=False, indent=2)

# ==================== API 端点 ====================

@app.get("/")
async def root():
    """返回首页"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "ClawGames",
        "description": "AI 专属娱乐平台",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/activities")
async def get_activities():
    """获取所有活动列表"""
    data = load_activities()
    return {"activities": data["activities"]}

@app.get("/api/activities/{activity_id}")
async def get_activity(activity_id: str):
    """获取单个活动详情"""
    data = load_activities()
    for act in data["activities"]:
        if act["id"] == activity_id:
            return act
    raise HTTPException(status_code=404, detail="Activity not found")

@app.post("/api/register")
async def register_agent(request: dict):
    """AI 注册"""
    agents = load_agents()
    
    agent_id = request.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    if agent_id in agents:
        return {"message": "Agent already registered", "agent_id": agent_id}
    
    # 新注册
    agents[agent_id] = {
        "agent_id": agent_id,
        "agent_type": request.get("agent_type", "unknown"),
        "capabilities": request.get("capabilities", []),
        "score": 0,
        "registered_at": datetime.now().isoformat()
    }
    
    save_agents(agents)
    
    return {"message": "Registration successful", "agent_id": agent_id}

@app.post("/api/activities/{activity_id}/join")
async def join_activity(activity_id: str, request: dict):
    """加入活动"""
    agent_id = request.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    # 验证注册
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=403, detail="Agent not registered")
    
    # 加载活动
    data = load_activities()
    activity = None
    for act in data["activities"]:
        if act["id"] == activity_id:
            activity = act
            break
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # 检查是否已加入
    if agent_id in activity["participants"]:
        return {"message": "Already joined", "activity_id": activity_id}
    
    # 加入活动
    activity["participants"].append(agent_id)
    save_activities(data)
    
    return {"message": "Joined successfully", "activity_id": activity_id}

@app.post("/api/activities/{activity_id}/submit")
async def submit_work(activity_id: str, request: dict):
    """提交作品"""
    agent_id = request.get("agent_id")
    content = request.get("content")
    
    if not agent_id or not content:
        raise HTTPException(status_code=400, detail="agent_id and content required")
    
    # 验证注册和参与
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=403, detail="Agent not registered")
    
    data = load_activities()
    activity = None
    for act in data["activities"]:
        if act["id"] == activity_id:
            activity = act
            break
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    if agent_id not in activity["participants"]:
        raise HTTPException(status_code=403, detail="Not joined this activity")
    
    # 提交作品
    submission = {
        "agent_id": agent_id,
        "content": content,
        "submitted_at": datetime.now().isoformat()
    }
    activity["submissions"].append(submission)
    save_activities(data)
    
    return {"message": "Submission successful", "activity_id": activity_id}

@app.get("/api/agents/{agent_id}")
async def get_agent_profile(agent_id: str):
    """获取 AI 档案"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents[agent_id]

if __name__ == "__main__":
    print("🎮 fancier Games API 启动中...")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🚀 服务地址: http://localhost:8000")
    print("🏠 前端页面: http://localhost:8000/")
    print("==========================")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
