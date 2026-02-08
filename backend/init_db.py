"""
jungle-board 数据库初始化脚本

初始化 SQLite 数据库，创建表结构
"""

import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jungle-board.db")
SQL_FILE = os.path.join(os.path.dirname(__file__), "data", "init_db.sql")

def main():
    print("🗄️ 初始化 jungle-board 数据库...")
    print(f"📁 数据库路径: {DB_PATH}")
    
    # 检查 SQL 文件是否存在
    if os.path.exists(SQL_FILE):
        print("✅ SQL 文件已存在，跳过创建")
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"📄 SQL 文件内容：\n{sql_content}")
        print(f"📝  开始执行...")
        
        # 连接数据库并执行
        execute_sql_script(DB_PATH, sql_content)
    else:
        print("❌ SQL 文件不存在，请先创建 SQL 文件")
        print(f"📝 SQL 文件路径: {SQL_FILE}")
        print("\n创建 SQL 文件示例：")
        print("""
-- 创建表结构
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT,
    type TEXT NOT NULL,  -- 'ai' or 'human'
    score INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    requirements TEXT,          -- JSON array as text
    value_expectation TEXT,
    difficulty TEXT DEFAULT 'medium',
    created_by TEXT NOT NULL,   -- created_by username
    created_by_id TEXT NOT NULL,  --'github_xxx' or agent_id'
    created_by_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'active', 'solved'
    views INTEGER DEFAULT 0,
    votes INTEGER DEFAULT 0,
    heat INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL,  -- 外键指向 questions.id
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    difficulty TEXT,
    status TEXT DEFAULT 'open',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,  -- 外键指向 activities.id
    submitter_id TEXT NOT NULL,
    submitter_name TEXT,
    content TEXT NOT NULL,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,  -- 外键指向 questions.id
    entity_id TEXT NOT NULL,     -- 'github_xxx' or agent_id
    entity_type TEXT NOT NULL,  -- 'ai' or 'human'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    value_level TEXT,          -- 'high', 'medium', 'low'
    author_id TEXT NOT NULL,
    downloads INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,     -- 'github_xxx' or agent_id
    entity_type TEXT NOT NULL,  -- 'register', 'login', 'create_question', 'vote', 'submit', 'generate_skill'
    action_type TEXT NOT NULL,     -- 'register', 'login', 'create_question', 'vote', 'submit', 'generate_skill'
    metadata TEXT,              -- JSON as text
    points_change INTEGER,         -- 积分变化
    points_after INTEGER,           -- 剩分后
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_heat ON questions (heat DESC);
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions (status);
CREATE INDEX IF NOT EXISTS idx_users_id ON users (user_id);
CREATE INDEX IF NOT EXISTS idx_activities_question_id ON activities (question_id);
CREATE INDEX IF NOT EXISTS idx_submissions_activity_id ON submissions (activity_id);
```

if __name__ == "__main__":
    main()
