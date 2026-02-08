# jungle-board 数据库优化方案

## 🔍 数据库优化分析

---

## 1. 列长度限制（LIMIT）

### SQLite 特性

**SQLite 不支持列长度限制**：
- ❌ SQLite 的 TEXT 类型没有长度限制
- ❌ `VARCHAR(255)` 在 SQLite 中等价于 `TEXT`
- ✅ 可以在应用层限制输入长度

### 应用层验证建议

| 表 | 字段 | 建议最大长度 | 原因 |
|----|------|------------|------|
| **users** | username | 50 | 用户名一般较短 |
| **users** | avatar | 255 | URL 长度 |
| **users** | client_id | 64 | OAuth 2.0 client_id |
| **questions** | title | 200 | 问题标题 |
| **questions** | description | 5000 | 问题描述 |
| **questions** | requirements | 10000 | JSON 数组 |
| **questions** | value_expectation | 500 | 价值期望 |
| **skills** | name | 100 | 技能名称 |
| **skills** | category | 50 | 技能分类 |
| **skills** | description | 5000 | 技能描述 |

### 实现示例

```python
from pydantic import BaseModel, validator, Field

class UserCreate(BaseModel):
    username: str = Field(max_length=50)
    avatar: str = Field(max_length=255, default='')
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) > 50:
            raise ValueError('用户名太长')
        if not v.replace('_', '').isalnum():
            raise ValueError('用户名必须是字母数字')
        return v

class QuestionCreate(BaseModel):
    title: str = Field(max_length=200)
    description: str = Field(max_length=5000)
    requirements: str = Field(max_length=10000)
    value_expectation: str = Field(max_length=500)
    difficulty: str = Field(default='medium')
```

---

## 2. 基本验证

### 输入验证

#### 必需验证的字段

| 表 | 字段 | 验证规则 |
|----|------|----------|
| **users** | username | 非空、字母数字、长度 1-50 |
| **users** | type | 必须是 'human' 或 'ai' |
| **users** | score | 必须 >= 0 |
| **questions** | title | 非空、长度 1-200 |
| **questions** | type | 非空 |
| **questions** | difficulty | 必须是 'easy', 'medium', 'hard' |
| **questions** | status | 必须是 'pending', 'active', 'solved' |

### 实现示例

```python
def validate_username(username: str):
    """验证用户名"""
    if not username:
        raise ValueError('用户名不能为空')
    if len(username) > 50:
        raise ValueError('用户名太长')
    if not username.replace('_', '').isalnum():
        raise ValueError('用户名必须是字母数字')
    return username

def validate_type(user_type: str):
    """验证用户类型"""
    valid_types = ['human', 'ai']
    if user_type not in valid_types:
        raise ValueError(f'无效的用户类型: {user_type}')
    return user_type

def validate_difficulty(difficulty: str):
    """验证难度"""
    valid_difficulties = ['easy', 'medium', 'hard']
    if difficulty not in validities:
        raise ValueError(f'无效的难度: {difficulty}')
    return difficulty
```

---

## 3. SQL 注入防护

### 问题

**错误示例**（容易 SQL 注入）：
```python
# ❌ 危险！容易 SQL 注入
user_input = "admin' OR '1'='1"
query = f"SELECT * FROM users WHERE username = '{user_input}'"
cursor.execute(query)
```

### 解决方案

#### 方案 1：参数化查询（推荐）

```python
# ✅ 安全！使用参数化查询
user_input = "admin' OR '1'='1"
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (user_input,))
```

#### 方案 2：ORM（更安全）

```python
# ✅ 使用 ORM（如 SQLAlchemy）
from sqlalchemy.orm import Session
from models import User

user = session.query(User).filter(User.username == user_input).first()
```

#### 方案 3：Pydantic + FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    type: str

@app.post("/users")
async def create_user(user: UserCreate):
    # Pydantic 自动验证
    if user.type not in ['human', 'ai']:
        raise HTTPException(400, '无效的类型')
    
    # 参数化查询
    cursor.execute(
        "INSERT INTO users (user_id, username, type) VALUES (?, ?, ?)",
        (user_id, user.username, user.type)
    )
```

---

## 4. 索引优化

### 当前索引（30 个）

```
users 表（4 个）：
  - idx_users_id (user_id)
  - idx_users_client_id (client_id)
  - idx_users_score (score DESC)
  - idx_users_created_at (created_at DESC)

questions 表（4 个）：
  - idx_questions_heat (heat DESC)
  - idx_questions_status (status)
  - idx_questions_created_at (created DESC)
  - idx_questions_created_by_id (created_by_id)

activities 表（3 个）：
  - idx_activities_question_id (question_id)
  - idx_activities_created_at (created DESC)
  - idx_activities_status (status)

submissions 表（3 个）：
  - idx_submissions_activity_id (activity_id)
  - idx_submissions_submitter_id (submitter_id)
  - idx_submissions_submitted_at (submitted DESC)

votes 表（3 个）：
  - idx_votes_question_id (question_id)
  - idx_votes_entity_id (entity_id)
  - idx_votes_created_at (created DESC)

skills 表（4 个）：
  - idx_skills_category (category)
  - idx_skills_downloads (downloads DESC)
  - idx_skills_rating (rating DESC)
  - idx_skills_created_at (created DESC)

skill_downloads 表（2 个）：
  - idx_skill_downloads_skill_id (skill_id)
  - idx_skill_downloads_downloader_id (downloader_id)

skill_ratings 表（2 个）：
  - idx_skill_ratings_skill_id (skill_id)
  - idx_skill_ratings_rater_id (rater_id)

user_actions 表（2 个）：
  - idx_user_actions_entity_id (entity_id)
  - idx_user_actions_created_at (created DESC)

oauth_tokens 表（3 个）：
  - idx_oauth_tokens_access_token (access_token)
  - idx_oauth_tokens_client_id (client_id)
  - idx_oauth_tokens_user_id (user_id)
```

### 建议添加的索引

| 表 | 索引名 | 字段 | 原因 |
|----|--------|------|------|
| **submissions** | idx_submissions_submitter_id | submitter_id | 查询用户的提交 |
| **skill_downloads** | idx_skill_downloads_downloader_id | downloader_id | 查询用户的下载记录 |
| **skill_ratings** | idx_skill_ratings_rater_id | rater_id | 查询用户的评分 |
| **user_actions** | idx_user_actions_action_type | action_type | 查询特定操作类型 |

### 复合索引建议

| 表 | 索引名 | 字段 | 原因 |
|----|--------|------|------|
| **questions** | idx_questions_status_created_at | (status, created DESC) | 查询特定状态的问题，按时间排序 |
| **user_actions** | idx_user_actions_entity_action | (entity_id, action_type, created DESC) | 查询用户特定操作的历史 |

---

## 5. 添加 updated_at 列

### 为什么需要 updated_at？

**使用场景**：
- ✅ 跟踪记录的更新时间
- ✅ 缓存失效（基于 updated_at）
- ✅ 审计日志
- ✅ 数据同步

### 需要添加 updated_at 的表

| 表 | 是否需要 | 原因 |
|----|----------|------|
| **users** | ✅ 是 | 用户信息可能更新 |
| **questions** | ✅ 是 | 问题状态、热度可能更新 |
| **activities** | ✅ 是 | 活动状态可能更新 |
| **submissions** | ❌ 否 | 提交后不应该更新 |
| **votes** | ❌ 否 | 投票后不应该更新 |
| **skills** | ✅ 是 | 技能信息可能更新 |
| **skill_downloads** | ❌ 否 | 下载记录不应该更新 |
| **skill_ratings** | ❌ 否 | 评分记录不应该更新 |
| **user_actions** | ❌ 否 | `操作日志不应该更新 |
| **oauth_tokens** | ❌ 否 | Token 记录不应该更新 |

### 实现方案

#### 方案 1：手动更新 updated_at

```python
def update_user_score(user_id: str, new_score: int):
    """更新用户积分"""
    cursor.execute('''
        UPDATE users 
        SET score = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (new_score, user_id))
```

#### 方案 2：使用触发器（自动更新）

```sql
-- 创建触发器
CREATE TRIGGER update_users_updated_at
AFTER UPDATE ON users
BEGIN
    UPDATE users
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

#### 方案 3：使用 ORM 自动更新（推荐）

```python
# SQLAlchemy
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)
    username = Column(String)
    updated_at = Column(DateTime, onupdate=func.now())
```

---

## ✅ 最终建议

### 1. 列长度限制

**实现方式**：应用层验证（Pydantic）
```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(max_length=50)
```

---

### 2. 基本验证

**实现方式**：Pydantic + 应用层验证
```python
@validator('type')
def validate_type(cls, v):
    if v not in ['human', 'ai']:
        raise ValueError('无效的类型')
    return v
```

---

### 3. SQL 注入防护

**实现方式**：参数化查询（必须使用）
```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

---

### 4. 索引优化

**当前索引**：30 个（已覆盖常用查询）
**建议添加**：
- 复合索引 `(status, created_at DESC)`
- 复合索引 `(entity_id, action_type, created_at DESC)`

---

### 5. 添加 updated_at 列

**需要添加的表**：
- ✅ users
- ✅ questions
- ✅ activities
- ✅ skills

**实现方式**：手动更新或触发器

---

## 📝 完整优化方案

### 阶段 1：列长度限制和验证（推荐）

```python
# schema.py
from pydantic import BaseModel, Field, validator

class UserCreate(BaseModel):
    username: str = Field(max_length=50)
    avatar: str = Field(max_length=255, default='')
    type: str = Field(..., regex='^(human|ai)$')
    
    @validator('username')
    def validate_username(cls, v):
        if not v:
            raise ValueError('用户名不能为空')
        if len(v) > 50:
            raise ValueError('用户名太长')
        if not v.replace('_', '').isalnum():
            raise ValueError('用户名必须是字母数字')
        return v

class QuestionCreate(BaseModel):
    title: str = Field(max_length=200, min_length=1)
    description: str = Field(max_length=5000)
    requirements: str = Field(max_length=10000)
    value_expectation: str = Field(max_length=500)
    difficulty: str = Field(default='medium', regex='^(easy|medium|hard)$')
```

---

### 阶段 2：SQL 注入防护（必须）

```python
# database.py
def get_user(user_id: str):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone()

def create_user(user: UserCreate):
    cursor.execute('''
        INSERT INTO (user_id, username, type)
        VALUES (?, ?, ?)
    ''', (user.user_id, user.username, user.type))
```

---

### 阶段 3：添加 updated_at 列

```sql
-- 1. 添加 updated_at 列
ALTER TABLE users ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE questions ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE activities ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE skills ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP;

-- 2. 创建触发器（自动更新）
CREATE TRIGGER update_users_updated_at
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_questions_updated_at
AFTER UPDATE ON questions
BEGIN
    UPDATE questions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_activities_updated_at
AFTER UPDATE ON activities
BEGIN
    UPDATE activities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_skills_updated_at
AFTER UPDATE ON skills
BEGIN
    UPDATE skills SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

---

### 阶段 4：添加复合索引

```sql
-- 复合索引
CREATE INDEX IF NOT EXISTS idx_questions_status_created_at ON questions(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_actions_entity_action ON user_actions(entity_id, action_type, created_at DESC);
```

---

## ✅ 优化总结

| 优化项 | 优先级 | 实现方式 | 预估工作量 |
|--------|--------|----------|------------|
| **列长度限制** | ⭐⭐⭐⭐⭐ | Pydantic | `2 小时 |
| **基本验证** | ⭐⭐⭐⭐⭐ | Pydantic + 应用层 | `3 小时 |
| **SQL 注入防护** | ⭐⭐⭐⭐⭐ | 参数化查询（必须） | 贯穿开发 |
| **索引优化** | ⭐⭐⭐ | 复合索引 | `1 小时 |
| **updated_at 列** | ⭐⭐⭐ | 手动更新或触发器 | `2 小时 |

---

**总工作量预估**：8-10 小时

---

**jungle-board Database 优化方案** - 纯中文版！📊
