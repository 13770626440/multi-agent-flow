"""
OpenMOSS 鉴权工具类

所有 OpenMOSS 鉴权逻辑收拢到此工具类，严禁在其他地方硬编码 Token。
OpenMOSS 服务端期望的鉴权格式: Authorization: Bearer <api_key>
"""
from app.core.token_manager import token_manager
from typing import Dict


class OpenMOSSAuth:
    """OpenMOSS 鉴权工具类"""

    @staticmethod
    def get_headers(role: str) -> Dict[str, str]:
        """
        获取 OpenMOSS 请求头

        Args:
            role: Agent 角色 (planner/executor/reviewer/patrol)

        Returns:
            包含 Authorization: Bearer <token> 的请求头
        """
        token = token_manager.get_token(role)
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def validate_token(role: str) -> bool:
        """
        验证 Token 是否有效

        Args:
            role: Agent 角色

        Returns:
            Token 是否有效
        """
        try:
            token_manager.get_token(role)
            return True
        except ValueError:
            return False
