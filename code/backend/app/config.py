from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, Dict, List
import os
import logging

logger = logging.getLogger(__name__)


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
    OPENMOSS_REGISTRATION_TOKEN: str = "maf-register-token-2026"  # Agent 注册令牌（与 OpenMOSS config.yaml 一致）
    
    # 模板配置
    TEMPLATE_DIR: str = "/app/templates"
    TEMPLATE_DEBOUNCE_SECONDS: float = 1.0  # 文件变更防抖动时间（秒）
    
    # Skills 配置
    SKILLS_DIR: str = "/app/skills"  # Skills 目录路径
    DEFAULT_ROLE_SKILL_MAP: Dict[str, List[str]] = {
        # 全局默认角色 → Skill 映射
        # 支持模板级覆盖（后续迭代）
        "product-manager": ["multi-agent-flow-manager"],
        "tech-lead": ["multi-agent-flow-manager"],
        "executor": ["agency-agent"],
        "reviewer": ["agency-agent"],
        "planner": ["multi-agent-flow-manager"],
        "patrol": ["agency-agent"],
    }
    
    # 任务管理配置
    SYNC_INTERVAL_SECONDS: int = 300  # 状态同步间隔（5 分钟）
    MAX_RETRIES: int = 3  # 最大重试次数
    DECOMPOSER_TIMEOUT: int = 600  # 分解任务超时（10 分钟）
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def validate_skills_config(self) -> None:
        """
        P2-6: 启动时验证 DEFAULT_ROLE_SKILL_MAP 中的 skills 是否存在
        """
        if not hasattr(self, 'SKILLS_DIR') or not hasattr(self, 'DEFAULT_ROLE_SKILL_MAP'):
            return
        
        skills_dir = self.SKILLS_DIR
        if not os.path.exists(skills_dir):
            logger.warning(f"Skills directory does not exist: {skills_dir}")
            return
        
        # 检查所有配置的 skill 是否存在
        all_configured_skills = set()
        for role, skills in self.DEFAULT_ROLE_SKILL_MAP.items():
            for skill in skills:
                all_configured_skills.add(skill)
                skill_path = os.path.join(skills_dir, skill, "SKILL.md")
                if not os.path.exists(skill_path):
                    logger.warning(f"Configured skill '{skill}' for role '{role}' not found at {skill_path}")
        
        logger.info(f"Validated {len(all_configured_skills)} configured skills: {sorted(all_configured_skills)}")


@lru_cache()
def get_settings() -> Settings:
    return Settings()