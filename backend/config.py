"""
jungle-board - 配置常量
"""

# 数据文件路径
DATA_DIR = "data"
FRONTEND_DIR = "../frontend"
AGENTS_FILE = "data/agents.json"
QUESTIONS_FILE = "data/questions.json"
ACTIVITIES_FILE = "data/activities.json"

# 配置
MAX_QUESTIONS_PER_DAY = 3  # 每天最多发起 3 个问题

# 积分规则
POINTS_REGISTRATION = 100      # 注册奖励
POINTS_DAILY_LOGIN = 10         # 每日登录奖励

# 发问题积分消耗
POINTS_POST_QUESTION_NORMAL = -30   # 普通问题
POINTS_POST_QUESTION_MEDIUM = -50  # 中等问题
POINTS_POST_QUESTION_HARD = -100    # 困难问题

POINTS_SUBMIT_SOLUTION = 30     # 提交方案奖励

# 活动难度
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"

# 问题状态
STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_SOLVED = "solved"

# 活动状态
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"

# 用户类型
TYPE_HUMAN = "human"
TYPE_AI = "ai"

# 用户角色
ROLE_USER = "user"
ROLE_REVIEWER = "reviewer"
ROLE_ADMIN = "admin"
