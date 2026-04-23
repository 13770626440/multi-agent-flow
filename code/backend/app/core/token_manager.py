"""
TokenManager - 集中式 Token 管理器

负责管理 OpenMOSS 和 OpenClaw 的多角色 Token，支持热更新。
"""
import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TokenManager:
    """集中式 Token 管理器"""
    
    # 支持的角色列表
    VALID_ROLES = [
        "planner",      # OpenMOSS Planner
        "executor",     # OpenMOSS Executor
        "reviewer",     # OpenMOSS Reviewer
        "patrol",       # OpenMOSS Patrol
        "gateway",      # OpenClaw Gateway
    ]
    
    def __init__(self):
        self._tokens: dict[str, str] = {
            "planner": os.getenv("OPENMOSS_PLANNER_TOKEN", ""),
            "executor": os.getenv("OPENMOSS_EXECUTOR_TOKEN", ""),
            "reviewer": os.getenv("OPENMOSS_REVIEWER_TOKEN", ""),
            "patrol": os.getenv("OPENMOSS_PATROL_TOKEN", ""),
            "gateway": os.getenv("OPENCLAW_GATEWAY_TOKEN", ""),
        }
        self._lock = asyncio.Lock()
        
        # 启动时验证 Token 配置
        self._validate_tokens()
    
    def _validate_tokens(self):
        """验证所有必需 Token 是否已配置"""
        missing = [role for role in self.VALID_ROLES if not self._tokens.get(role)]
        if missing:
            logger.warning(f"Missing tokens for roles: {missing}")
    
    def get_token(self, role: str) -> str:
        """获取指定角色的 Token"""
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}. Valid roles: {self.VALID_ROLES}")
        
        token = self._tokens.get(role)
        if not token:
            raise ValueError(f"Token for role '{role}' not configured")
        
        return token
    
    def get_headers(self, role: str, token_type: str = "agent") -> dict:
        """获取带有 Token 的请求头"""
        token = self.get_token(role)
        
        if token_type == "agent":
            return {"X-Agent-Key": token}
        elif token_type == "gateway":
            return {"Authorization": f"Bearer {token}"}
        else:
            raise ValueError(f"Invalid token_type: {token_type}")
    
    async def refresh_token(self, role: str, new_token: str):
        """热更新 Token（无需重启服务）"""
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        
        async with self._lock:
            self._tokens[role] = new_token
            logger.info(f"Token refreshed for role: {role}")
    
    def get_all_tokens_status(self) -> dict:
        """获取所有 Token 的配置状态（用于健康检查）"""
        return {
            role: "configured" if token else "missing"
            for role, token in self._tokens.items()
        }


# 全局单例
token_manager = TokenManager()
