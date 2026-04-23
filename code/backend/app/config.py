from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Multi-Agent-Flow Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://maf_user:maf_password@postgres:5432/maf_db"

    # 外部服务配置
    OPENMOSS_BASE_URL: str = "http://openmoss:6565"
    OPENCLAW_BASE_URL: str = "http://openclaw-gateway:18789"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
