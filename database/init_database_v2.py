"""
jungle-board 数据库初始化脚本（改进版 v2.0）

初始化 SQLite 数据库，创建所有表结构
每张表使用独立的方法创建

改进内容（v2.0）：
- 优化 oauth_tokens 表：添加 revoked, revoked_at, last_used_at 字段
- 添加 submissions 投票机制：创建 submission_votes 表
- 在 submissions 表添加投票相关字段：vote_count, rank, winner
- 添加角色系统（role 字段）

- 添加 updated_at 字段
- 添加触发器（自动更新 updated_at）
- 添加复合索引
- 启用外键约束
"""

import sqlite3
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime

def get_database_path():
    """
    获取数据库路径（跨平台、多环境）
    
    优先级：
    1. 环境变量 JUNGLE_BOARD_DB_PATH
    2. XDG 标准目录（开发环境）
    3. /data/jungle-board.db（生产/容器）
    4. 项目根目录（回退）
    """
    # 1. 环境变量优先
    if 'JUNGLE_BOARD_DB_PATH' in os.environ:
        return Path(os.environ['JUNGLE_BOARD_DB_PATH'])
    
    # 2. XDG 标准目录
    if sys.platform == 'linux':
        data_dir = Path.home() / '.local' / 'share' / 'jungle-board'
    elif sys.platform == 'darwin':
        data_dir = Path.home() / 'Library' / 'Application Support' / 'jungle-board'
    elif os.name == 'nt':
        appdata = os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')
        data_dir = Path(appdata) / 'jungle-board'
    else:
        # 3. 生产/容器默认路径
        data_dir = Path('/data')
    
    # 创建目录
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir / 'jungle-board.db'

# 数据库路径
DB_PATH = get_database_path()

def get_connection():
    """获取数据库连接，启用外键约束"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def hash_token(token):
    """对 access_token 进行 SHA256 哈希（安全存储）"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_users_table(conn):
    """创建 users 表 - 用户信息"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT,
            avatar TEXT,
            type TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            client_id TEXT UNIQUE,
            client_secret_hash TEXT,
            score INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created users table")

def create_questions_table(conn):
    """创建 questions 表 - 问题信息"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NOT NULL,
            type TEXT NOT NOT NULL,
            description TEXT,
            requirements TEXT NOT NOT NULL,
            value_expectation TEXT,
            difficulty TEXT DEFAULT 'medium',
            
            created_by_id TEXT NOT NULL,
            
            status TEXT DEFAULT 'pending',
            
            views INTEGER DEFAULT 0,
            votes INTEGER DEFAULT 0,
            participants INTEGER DEFAULT 0,
            heat INTEGER DEFAULT 0,
            
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created questions table")

def create_activities_table(conn):
    """创建 activities 表 - 每日活动"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            title TEXT NOT NOT NULL,
            type TEXT NOT NOT NULL,
            description TEXT,
            requirements TEXT,
            difficulty TEXT,
            
            status TEXT DEFAULT 'open',
            
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created activities table")

def create_submissions_table(conn):
    """创建 submissions 表 - 方案提交（改进版 v2.0）"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            submitter_id TEXT NOT NULL,
            submitter_name TEXT NOT NULL,
            content TEXT NOT NULL,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            -- 新增字段（v2.0）
            vote_count INTEGER DEFAULT 0,
            rank INTEGER DEFAULT 0,
            winner INTEGER DEFAULT 0
        )
    ''')
    print("✅ Created submissions table (v2.0 with voting)")

def create_submission_votes_table(conn):
    """创建 submission_votes 表 - 方案投票（新增 v2.0）"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS submission_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            entity_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            vote INTEGER NOT NULL,
            voted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE (submission_id, entity_id),
            FOREIGN KEY (submission_id) REFERENCES submissions(id)
        )
    ''')
    print("✅ Created submission_votes table (v2.0)")

def create_votes_table(conn):
    """创建 votes 表 - 问题投票"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            entity_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            vote INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE (question_id, entity_id)
        )
    ''')
    print("✅ Created votes table")

def create_skills_table(conn):
    """创建 skills 表 - 技能资产"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NOT NULL,
            category TEXT NOT NOT NULL,
            description TEXT,
            value_level TEXT,
            author_id TEXT NOT NULL,
            author_name TEXT NOT NULL,
            
            downloads INTEGER DEFAULT 0,
            rating REAL DEFAULT 0.0,
            rating_count INTEGER DEFAULT 0,
            
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created skills table")

def create_skill_downloads_table(conn):
    """创建 skill_downloads 表 - 技能下载记录"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS skill_downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            downloader_id TEXT NOT NULL,
            downloaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created skill_downloads table")

def create_skill_ratings_table(conn):
    """创建 skill_ratings 表 - 技能评分"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS skill_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            rater_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            rated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created skill_ratings table")

def create_user_actions_table(conn):
    """创建 user_actions 表 - 用户操作日志"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            action_type TEXT NOT NULL,
            metadata TEXT,
            points_change INTEGER,
            points_after INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created user_actions table")

def create_oauth_tokens_table(conn):
    """创建 oauth_tokens 表 - OAuth 2.0 access_token（改进版 v2.0）"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token_hash TEXT UNIQUE NOT NULL,
            client_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            
            -- 新增字段（v2.0）
            revoked INTEGER DEFAULT 0,
            revoked_at TEXT,
            last_used_at TEXT,
            
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created oauth_tokens table (v2.0 with revocation support)")

def create_triggers(conn):
    """创建触发器（自动更新 updated_at）"""
    # users 表触发器
    try:
        conn.execute('''
            CREATE TRIGGER update_users_updated_at
            AFTER UPDATE ON users
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        print("✅ Created trigger: update_users_updated_at")
    except sqlite3.OperationalError:
        print("⚠️  Trigger already exists: update_users_updated_at")
    
    # questions 表触发器
    try:
        conn.execute('''
            CREATE TRIGGER update_questions_updated_at
            AFTER UPDATE ON questions
            BEGIN
                UPDATE questions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        print("✅ Created trigger: update_questions_updated_at")
    except sqlite3.OperationalError:
        print("⚠️  Trigger already exists: update_questions_updated_at")
    
    # activities 表触发器
    try:
        conn.execute('''
            CREATE TRIGGER update_activities_updated_at
            AFTER UPDATE ON activities
            BEGIN
                UPDATE activities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        print("✅ Created trigger: update_activities_updated_at")
    except sqlite3.OperationalError:
        print("⚠️  Trigger already exists: update_activities_updated_at")
    
    # skills 表触发器
    try:
        conn.execute('''
            CREATE TRIGGER update_skills_updated_at
            AFTER UPDATE ON skills
            BEGIN
                UPDATE skills SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        print("✅ Created trigger: update_skills_updated_at")
    except sqlite3.OperationalError:
        print("⚠️  Trigger already exists: update_skills_updated_at")

def create_indexes(conn):
    """创建索引"""
    # users 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_id ON users(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_client_id ON users(client_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_score ON users(score DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC)')
    print("✅ Created indexes for users table")
    
    # questions 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_questions_heat ON questions(heat DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_questions_created_by_id ON questions(created_by_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_questions_status_created_at ON questions(status, created_at DESC)')
    print("✅ Created indexes for questions table")
    
    # activities 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_activities_question_id ON activities(question_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status)')
    print("✅ Created indexes for activities table")
    
    # submissions 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_submissions_activity_id ON submissions(activity_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_submissions_submitter_id ON submissions(submitter_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions(submitted_at DESC)')
    print("✅ Created indexes for submissions table")
    
    # submission_votes 表索引（新增 v2.0）
    conn.execute('CREATE INDEX IF NOT EXISTS idx_submission_votes_submission_id ON submission_votes(submission_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_submission_votes_entity_id ON submission_votes(entity_id)')
    print("✅ Created indexes for submission_votes table (v2.0)")
    
    # votes 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_votes_question_id ON votes(question_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_votes_entity_id ON votes(entity_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_votes_created_at ON votes(created_at DESC)')
    print("✅ Created indexes for votes table")
    
    # skills 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skills_downloads ON skills(downloads DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skills_rating ON skills(rating DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skills_created_at ON skills(created_at DESC)')
    print("✅ Created indexes for skills table")
    
    # skill_downloads 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skill_downloads_skill_id ON skill_downloads(skill_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skill_downloads_downloader_id ON skill_downloader(downloader_id)')
    print("✅ Created indexes for skill_downloads table")
    
    # skill_ratings 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skill_ratings_skill_id ON skill_ratings(skill_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_skill_ratings_rater_id ON skill_ratings(rater_id)')
    print("✅ Created indexes for skill_ratings table")
    
    # user_actions 表索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_user_actions_entity_id ON user_actions(entity_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_user_actions_action_type ON user_actions(action_type)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_user_actions_entity_action ON user_actions(entity_id, action_type, created_at DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_user_actions_created_at ON user_actions(created_at DESC)')
    print("✅ Created indexes for user_actions table")
    
    # oauth_tokens 表索引（改进版 v2.0）
    conn.execute('CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_tokens(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_oauth_tokens_client_id ON oauth_tokens(client_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_oauth_tokens_expires_at ON oauth_tokens(expires_at)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_oauth_tokens_last_used_at ON oauth_tokens(last_used_at DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_oauth_tokens_revoked ON oauth_tokens(revoked)')
    print("✅ Created indexes for oauth_tokens table (v2.0)")

def insert_sample_data(conn):
    """插入示例数据"""
    # 插入示例用户
    try:
        conn.execute('''
            INSERT INTO users (user_id, username, type, role, score)
            VALUES
                ('admin_001', 'admin', 'human', 'admin', 0),
                ('reviewer_001', 'reviewer', 'human', 'reviewer', 0),
                ('github_12345', 'zhangtao', 'human', 'user', 100)
        ''')
        print("✅ Inserted sample users")
    except sqlite3.IntegrityError:
        print("⚠️  Sample users already exist")
    
    # 插入示例问题
    try:
        conn.execute('''
            INSERT INTO questions (
                title, type, description, requirements, 
                value_expectation, difficulty, created_by_id
            )
            VALUES (
                'Excel 批量数据处理',
                'data_processing',
                'HR 部门需要处理 1000+ 员工的 Excel 表格，批量计算年终奖',
                '["实现批量读取", "实现年终奖计算公式", "生成汇总表"]',
                '避免手动计算，提高准确性',
                'medium',
                'github_12345'
            )
        ''')
        print("✅ Inserted sample question")
    except sqlite3.IntegrityError:
        print("⚠️  Sample question already exists")

def init_database():
    """初始化数据库"""
    print("🗄️  Initializing jungle-board database v2.0...")
    print(f"📁 Database path: {DB_PATH}")
    print()
    
    conn = get_connection()
    
    try:
        # 创建所有表
        print("📊 Creating tables...")
        create_users_table(conn)
        create_questions_table(conn)
        create_activities_table(conn)
        create_submissions_table(conn)
        create_votes_table(conn)
        create_skills_table(conn)
        create_skill_downloads_table(conn)
        create_skill_ratings_table(conn)
        create_user_actions_table(conn)
        create_oauth_tokens_table(conn)
        
        # 创建 submission_votes 表（v2.0 新增）
        create_submission_votes_table(conn)
        
        print()
        
        # 创建触发器
        print("🔧 Creating triggers...")
        create_triggers(conn)
        print()
        
        # 创建索引
        print("📈 Creating indexes...")
        create_indexes(conn)
        print()
        
        # 插入示例数据
        print("📝 Inserting sample data...")
        insert_sample_data(conn)
        print()
        
        # 提交更改
        conn.commit()
        print("✅ Database initialized successfully (v2.0)!")
        print(f"✅ Database file: {DB_PATH}")
        print()
        print("🎉 New features in v2.0:")
        print("   • Submissions voting mechanism (submission_votes table)")
        print("   • OAuth token revocation support (revoked, revoked_at, last_used_at)")
        print("   • Submission ranking system (vote_count, rank, winner fields)")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        conn.close()

def reset_database():
    """重置数据库（删除所有表）"""
    print("⚠️  This will delete all data!")
    response = input("Are you sure? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print("🗑️  Resetting database...")
    
    conn = get_connection()
    
    try:
        # 删除所有表
        tables = [
            'users', 'questions', 'activities', 'submissions',
            'votes', 'skills', 'skill_downloads', 'skill_ratings',
            'user_actions', 'oauth_tokens', 'submission_votes'
        ]
        
        for table in tables:
            conn.execute(f'DROP TABLE IF EXISTS {table}')
            print(f"🗑️  Dropped {table} table")
        
        conn.commit()
        print("✅ Database reset successfully!")
        
        # 重新初始化
        init_database()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error resetting database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'reset':
            reset_database()
        else:
            print("Usage: python init_database_v2.py [reset]")
            sys.exit(1)
    else:
        init_database()
