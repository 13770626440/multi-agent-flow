"""
OpenMOSSAuth 单元测试

测试覆盖：
1. get_headers() 正确生成 Authorization header
2. validate_token() 验证 Token 有效性
3. 异常场景处理
"""
import pytest
import os
from unittest.mock import patch

from app.clients.openmoss_auth import OpenMOSSAuth
from app.core.token_manager import token_manager


class TestOpenMOSSAuth:
    """OpenMOSSAuth 单元测试"""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """确保测试环境中存在 Token"""
        os.environ["OPENMOSS_PLANNER_TOKEN"] = "test_planner_key"
        os.environ["OPENMOSS_EXECUTOR_TOKEN"] = "test_executor_key"
        os.environ["OPENMOSS_PATROL_TOKEN"] = "test_patrol_key"
        os.environ["OPENMOSS_REVIEWER_TOKEN"] = "test_reviewer_key"
        # 刷新单例以加载新 Token
        token_manager._tokens.update({
            "planner": "test_planner_key",
            "executor": "test_executor_key",
            "patrol": "test_patrol_key",
            "reviewer": "test_reviewer_key",
            "gateway": "test_gateway_key"
        })

    def test_get_headers_planner(self):
        """测试获取 Planner 角色请求头"""
        headers = OpenMOSSAuth.get_headers("planner")
        assert headers == {"Authorization": "Bearer test_planner_key"}

    def test_get_headers_executor(self):
        """测试获取 Executor 角色请求头"""
        headers = OpenMOSSAuth.get_headers("executor")
        assert headers == {"Authorization": "Bearer test_executor_key"}

    def test_get_headers_patrol(self):
        """测试获取 Patrol 角色请求头"""
        headers = OpenMOSSAuth.get_headers("patrol")
        assert headers == {"Authorization": "Bearer test_patrol_key"}

    def test_get_headers_reviewer(self):
        """测试获取 Reviewer 角色请求头"""
        headers = OpenMOSSAuth.get_headers("reviewer")
        assert headers == {"Authorization": "Bearer test_reviewer_key"}

    def test_get_headers_invalid_role(self):
        """测试获取无效角色请求头应抛出异常"""
        with pytest.raises(ValueError, match="Invalid role"):
            OpenMOSSAuth.get_headers("invalid_role")

    def test_validate_token_valid(self):
        """测试验证有效 Token"""
        assert OpenMOSSAuth.validate_token("planner") is True
        assert OpenMOSSAuth.validate_token("executor") is True

    def test_validate_token_invalid(self):
        """测试验证无效 Token"""
        assert OpenMOSSAuth.validate_token("invalid_role") is False
