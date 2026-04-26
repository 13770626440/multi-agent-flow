from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Multi-Agent-Flow Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://maf_user:maf_password@postgres:5432/maf_db"
    
    # Redis 配置
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 10  # 连接池最大连接数
    
    # 外部服务配置
    OPENMOSS_BASE_URL: str = "http://openmoss:6565"
    OPENCLAW_BASE_URL: str = "http://openclaw-gateway:18789"
    
    # OpenMOSS Token 配置
    OPENMOSS_TOKEN_PLANNER: Optional[str] = None
    OPENMOSS_TOKEN_EXECUTOR: Optional[str] = None
    OPENMOSS_TOKEN_REVIEWER: Optional[str] = None
    OPENMOSS_TOKEN_PATROL: Optional[str] = None
    
    # 模板配置
    TEMPLATE_DIR: str = "/app/templates"
    TEMPLATE_DEBOUNCE_SECONDS: float = 1.0  # 文件变更防抖动时间（秒）
    
    # 任务管理配置
    SYNC_INTERVAL_SECONDS: int = 300  # 状态同步间隔（5 分钟）
    MAX_RETRIES: int = 3  # 最大重试次数
    DECOMPOSER_TIMEOUT: int = 600  # 分解任务超时（10 分钟）
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()