"""应用配置"""
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# MySQL 数据库配置
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "pz_medical",
    "charset": "utf8mb4",
}

# JWT 配置
JWT_SECRET_KEY = "pz_medical_secret_key_2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440  # 24小时

# 服务配置
APP_HOST = "0.0.0.0"
APP_PORT = 2306
APP_PREFIX = "/v3pz"

# AI Agent 配置（从环境变量读取）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 高德地图 API（从环境变量读取）
AMAP_KEY = os.getenv("AMAP_KEY", "")
AMAP_STATIC_MAP_URL = os.getenv("AMAP_STATIC_MAP_URL", "https://restapi.amap.com/v3/staticmap")
