"""
jungle-board - 数据库模块
"""

import sqlite3
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import os
import sys
from pathlib import Path

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
DB_PATH = str(get_database_path())


@contextmanager
def get_db():
    """获取数据库连接（上下文管理器）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典格式
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==================== 通用数据库操作 ====================

def dict_from_row(row: sqlite3.Row) -> Dict:
    """将 sqlite3.Row 转换为字典"""
    return dict(row) if row else {}


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict]:
    """将 sqlite3.Row 列表转换为字典列表"""
    return [dict(row) for row in rows]


# ==================== Users 表操作 ====================

def get_user(user_id: str) -> Optional[Dict]:
    """获取用户信息"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        return dict_from_row(cursor.fetchone())


def create_user(user_data: Dict) -> str:
    """创建用户"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO users (
                user_id, username, avatar, type, role,
                client_id, client_secret_hash, score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data.get("user_id"),
            user_data.get("username"),
            user_data.get("avatar", ""),
            user_data.get("type", "human"),
            user_data.get("role", "user"),
            user_data.get("client_id"),
            user_data.get("client_secret_hash"),
            user_data.get("score", 0)
        ))
        return user_data.get("user_id")


def update_user_score(user_id: str, new_score: int) -> bool:
    """更新用户积分"""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET score = ? WHERE user_id = ?",
            (new_score, user_id)
        )
        return True


def list_users(limit: int = 100, offset: int = 0) -> List[Dict]:
    """列出用户（分页）"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM users
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return rows_to_list(cursor.fetchall())


# ==================== Questions 表操作 ====================

def get_question(question_id: int) -> Optional[Dict]:
    """获取问题信息"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM questions WHERE id = ?",
            (question_id,)
        )
        return dict_from_row(cursor.fetchone())


def create_question(question_data: Dict) -> int:
    """创建问题"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO questions (
                title, type, description, requirements,
                value_expectation, difficulty, created_by_id,
                status, views, votes, participants, heat
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_data.get("title"),
            question_data.get("type"),
            question_data.get("description"),
            question_data.get("requirements", "[]"),
            question_data.get("value_expectation", ""),
            question_data.get("difficulty", "medium"),
            question_data.get("created_by_id"),
            question_data.get("status", "pending"),
            question_data.get("views", 0),
            question_data.get("votes", 0),
            question_data.get("participants", "[]"),
            question_data.get("heat", 0)
        ))
        return cursor.lastrowid


def list_questions(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """列出问题（可按状态筛选）"""
    with get_db() as conn:
        if status:
            cursor = conn.execute("""
                SELECT * FROM questions
                WHERE status = ?
                ORDER BY heat DESC, created_at DESC
                LIMIT ? OFFSET ?
            """, (status, limit, offset))
        else:
            cursor = conn.execute("""
                SELECT * FROM questions
                ORDER BY heat DESC, created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        return rows_to_list(cursor.fetchall())


def increment_question_views(question_id: int) -> bool:
    """增加问题浏览次数"""
    with get_db() as conn:
        conn.execute(
            "UPDATE questions SET views = views + 1 WHERE id = ?",
            (question_id,)
        )
        return True


def increment_question_votes(question_id: int) -> bool:
    """增加问题投票数"""
    with get_db() as conn:
        conn.execute(
            "UPDATE questions SET votes = votes + 1 WHERE id = ?",
            (question_id,)
        )
        return True


def update_question_status(question_id: int, status: str) -> bool:
    """更新问题状态"""
    with get_db() as conn:
        conn.execute(
            "UPDATE questions SET status = ? WHERE id = ?",
            (status, question_id)
        )
        return True


def get_today_question_count(user_id: str) -> int:
    """获取用户今天发起的问题数量"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM questions
            WHERE created_by_id = ?
            AND DATE(created_at) = DATE('now')
        """, (user_id,))
        row = cursor.fetchone()
        return row["count"] if row else 0


# ==================== Votes 表操作 ====================

def has_voted(question_id: int, entity_id: str) -> bool:
    """检查是否已投票"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM votes
            WHERE question_id = ? AND entity_id = ?
        """, (question_id, entity_id))
        row = cursor.fetchone()
        return row["count"] > 0 if row else False


def create_vote(vote_data: Dict) -> int:
    """创建投票"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO votes (
                question_id, entity_id, entity_type, vote
            ) VALUES (?, ?, ?, ?)
        """, (
            vote_data.get("question_id"),
            vote_data.get("entity_id"),
            vote_data.get("entity_type"),
            vote_data.get("vote", True)
        ))
        return cursor.lastrowid


# ==================== Activities 表操作 ====================

def get_activity(activity_id: int) -> Optional[Dict]:
    """获取活动信息"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM activities WHERE id = ?",
            (activity_id,)
        )
        return dict_from_row(cursor.fetchone())


def create_activity(activity_data: Dict) -> int:
    """创建活动"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO activities (
                question_id, title, type, description,
                requirements, difficulty, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_data.get("question_id"),
            activity_data.get("title"),
            activity_data.get("type"),
            activity_data.get("description"),
            activity_data.get("requirements", "[]"),
            activity_data.get("difficulty"),
            activity_data.get("status", "open")
        ))
        return cursor.lastrowid


def list_activities(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """列出活动（可按状态筛选）"""
    with get_db() as conn:
        if status:
            cursor = conn.execute("""
                SELECT * FROM activities
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (status, limit, offset))
        else:
            cursor = conn.execute("""
                SELECT * FROM activities
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        return rows_to_list(cursor.fetchall())


def update_activity_status(activity_id: int, status: str) -> bool:
    """更新活动状态"""
    with get_db() as conn:
        conn.execute(
            "UPDATE activities SET status = ? WHERE id = ?",
            (status, activity_id)
        )
        return True


# ==================== Submissions 表操作 ====================

def get_submissions(activity_id: int) -> List[Dict]:
    """获取活动的所有提交"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM submissions
            WHERE activity_id = ?
            ORDER BY submitted_at DESC
        """, (activity_id,))
        return rows_to_list(cursor.fetchall())


def create_submission(submission_data: Dict) -> int:
    """创建提交"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO submissions (
                activity_id, submitter_id, submitter_name, content
            ) VALUES (?, ?, ?, ?)
        """, (
            submission_data.get("activity_id"),
            submission_data.get("submitter_id"),
            submission_data.get("submitter_name"),
            submission_data.get("content")
        ))
        return cursor.lastrowid


# ==================== Skills 表操作 ====================

def get_skill(skill_id: int) -> Optional[Dict]:
    """获取技能信息"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM skills WHERE id = ?",
            (skill_id,)
        )
        return dict_from_row(cursor.fetchone())


def create_skill(skill_data: Dict) -> int:
    """创建技能"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO skills (
                name, category, description, value_level,
                author_id, author_name
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            skill_data.get("name"),
            skill_data.get("category"),
            skill_data.get("description"),
            skill_data.get("value_level"),
            skill_data.get("author_id"),
            skill_data.get("author_name")
        ))
        return cursor.lastrowid


def list_skills(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """列出技能（可按分类筛选）"""
    with get_db() as conn:
        if category:
            cursor = conn.execute("""
                SELECT * FROM skills
                WHERE category = ?
                ORDER BY rating DESC, downloads DESC
                LIMIT ? OFFSET ?
            """, (category, limit, offset))
        else:
            cursor = conn.execute("""
                SELECT * FROM skills
                ORDER BY rating DESC, downloads DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        return rows_to_list(cursor.fetchall())


# ==================== User Actions 表操作 ====================

def create_user_action(action_data: Dict) -> int:
    """创建用户操作日志"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO user_actions (
                entity_id, entity_type, action_type,
                metadata, points_change, points_after
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            action_data.get("entity_id"),
            action_data.get("entity_type"),
            action_data.get("action_type"),
            action_data.get("metadata", "{}"),
            action_data.get("points_change"),
            action_data.get("points_after")
        ))
        return cursor.lastrowid


def get_user_actions(
    entity_id: str,
    action_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """获取用户操作日志"""
    with get_db() as conn:
        if action_type:
            cursor = conn.execute("""
                SELECT * FROM user_actions
                WHERE entity_id = ? AND action_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (entity_id, action_type, limit))
        else:
            cursor = conn.execute("""
                SELECT * FROM user_actions
                WHERE entity_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (entity_id, limit))
        return rows_to_list(cursor.fetchall())
