#!/bin/bash
# ClawGames 启动脚本

cd "$(dirname "$0")"

echo "🎮 ClawGames 启动中..."
echo "📖 API 文档: http://localhost:8000/docs"
echo "🚀 服务地址: http://localhost:8000"
echo "=========================="

# 启动服务器
cd backend
../venv/bin/python server.py
