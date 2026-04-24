"""
ReviewEngine 集成测试（Mock OpenMOSS API）

测试评审引擎与 OpenMOSS 的集成：
1. 创建评审任务
2. 处理评审驳回（创建修正任务）
"""
import pytest
import respx
import httpx
from app.core.review_engine import ReviewEngine


# Mock 配置
OPENMOSS_BASE_URL = "http://openmoss:6565"


class TestReviewEngineIntegration:
    """ReviewEngine 集成测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.engine = ReviewEngine()
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_create_review_task(self):
        """TC-REVIEW-02: 测试创建评审任务（Mock OpenMOSS）"""
        # 注入测试 Token
        from app.core.token_manager import token_manager
        await token_manager.refresh_token("planner", "test_planner_token")
        
        # Mock OpenMOSS API
        respx.post(f"{OPENMOSS_BASE_URL}/api/sub-tasks").mock(
            return_value=httpx.Response(200, json={
                "id": "om_review_001",
                "task_id": "task_001",
                "name": "评审：数据库设计",
                "status": "pending"
            })
        )
        
        sub_task = {
            "id": "sub_001",
            "task_id": "task_001",
            "name": "数据库设计",
            "acceptance": "- 输出 ER 图\n- 输出 DDL 脚本"
        }
        
        result = await self.engine.handle_task_review(sub_task)
        
        # 验证返回结果
        assert result is not None
        assert result.get("id") == "om_review_001"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_handle_review_failed(self):
        """TC-REVIEW-03: 测试处理评审驳回（Mock OpenMOSS）"""
        # Mock OpenMOSS API（创建修正任务）
        respx.post(f"{OPENMOSS_BASE_URL}/api/sub-tasks").mock(
            return_value=httpx.Response(200, json={
                "id": "om_rework_001",
                "task_id": "task_001",
                "name": "修正：数据库设计",
                "status": "pending"
            })
        )
        
        # Mock OpenClaw API（派发任务）
        respx.post("http://openclaw-gateway:18789/api/v1/message").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        
        # 注入测试 Token
        from app.core.token_manager import token_manager
        await token_manager.refresh_token("gateway", "test_gateway_token")
        
        sub_task = {
            "id": "sub_001",
            "task_id": "task_001",
            "name": "数据库设计",
            "role": "database",
            "instruction": "设计用户表结构",
            "acceptance": "- 输出 ER 图",
            "assigned_agent": "db_agent_001"
        }
        comments = "ER 图缺少外键关系"
        
        result = await self.engine.handle_review_failed(sub_task, comments)
        
        # 验证返回结果
        assert result is not None
        assert result.get("openmoss_id") == "om_rework_001"
        assert "ER 图缺少外键关系" in result.get("instruction", "")