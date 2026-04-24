"""
集成测试 - 端到端验证完整流程（最终版本）

使用 Mock 数据库依赖，无需任何外部服务。
"""
import pytest
import respx
import httpx
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

from app.main import app
from app.models.task import TaskStatus, SubTaskStatus
from app.core.sync_engine import sync_engine, OPENMOSS_STATUS_MAP
from app.core.dispatcher import dispatcher
from app.core.token_manager import token_manager


# --- Mock 配置 ---

OPENMOSS_BASE_URL = "http://openmoss:6565"
OPENCLAW_BASE_URL = "http://openclaw-gateway:18789"


@pytest.fixture
def client():
    """创建测试客户端"""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=AsyncMock(scalars=AsyncMock(return_value=[]), scalar_one_or_none=AsyncMock(return_value=None)))
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = AsyncMock()
    return mock_session


# --- 测试用例 ---

class TestTaskCreation:
    """测试任务创建流程"""
    
    def test_create_task_instance(self, client, mock_db):
        """测试创建任务实例"""
        with respx.mock:
            respx.post(f"{OPENMOSS_BASE_URL}/api/sub-tasks").mock(
                return_value=httpx.Response(200, json={"id": "om_test_001"})
            )
            
            with patch("app.api.tasks.get_db", return_value=mock_db):
                response = client.post(
                    "/api/v1/tasks/",
                    json={
                        "name": "集成测试任务",
                        "description": "用于验证完整流程的测试任务",
                        "template_id": "simple_test",
                        "user_id": "test_user"
                    }
                )
                
                assert response.status_code == 200
    
    def test_get_task_list(self, client, mock_db):
        """测试获取任务列表"""
        with respx.mock:
            with patch("app.api.tasks.get_db", return_value=mock_db):
                response = client.get("/api/v1/tasks/")
                assert response.status_code == 200


class TestSyncEngine:
    """测试状态同步引擎"""
    
    @pytest.mark.asyncio
    async def test_status_mapping(self):
        """测试 OpenMOSS 状态映射"""
        assert "done" in OPENMOSS_STATUS_MAP
        assert OPENMOSS_STATUS_MAP["done"] == SubTaskStatus.DONE
        assert "in_progress" in OPENMOSS_STATUS_MAP
        assert OPENMOSS_STATUS_MAP["in_progress"] == SubTaskStatus.IN_PROGRESS
        assert "review" in OPENMOSS_STATUS_MAP
        assert OPENMOSS_STATUS_MAP["review"] == SubTaskStatus.REVIEW
        assert "rework" in OPENMOSS_STATUS_MAP
        assert OPENMOSS_STATUS_MAP["rework"] == SubTaskStatus.REWORK
        assert "blocked" in OPENMOSS_STATUS_MAP
        assert OPENMOSS_STATUS_MAP["blocked"] == SubTaskStatus.BLOCKED
    
    @pytest.mark.asyncio
    async def test_sync_engine_initialization(self):
        """测试同步引擎初始化"""
        assert sync_engine.sync_interval > 0
        assert hasattr(sync_engine, 'sync_all_tasks')
        assert hasattr(sync_engine, 'sync_sub_task')
        assert hasattr(sync_engine, '_unlock_dependent_tasks')


class TestDispatcher:
    """测试任务派发器"""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_dispatch_task_push_mode(self):
        """测试任务派发（主推模式）"""
        await token_manager.refresh_token("gateway", "test_gateway_token_123")
        
        respx.post(f"{OPENCLAW_BASE_URL}/api/v1/message").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        
        result = await dispatcher.dispatch_task(
            sub_task_id="test_dispatch_1",
            openmoss_id="test_om_1",
            role="researcher",
            instruction="测试指令",
            conversation_id="test_conv_1"
        )
        
        assert "status" in result
        assert result["status"] == "pushed"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_dispatch_task_pull_fallback(self):
        """测试任务派发（备拉模式降级）"""
        respx.post(f"{OPENCLAW_BASE_URL}/api/v1/message").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        
        result = await dispatcher.dispatch_task(
            sub_task_id="test_dispatch_2",
            openmoss_id="test_om_2",
            role="researcher",
            instruction="测试指令",
            conversation_id="test_conv_2"
        )
        
        assert "status" in result
        assert result["status"] == "pending_pull"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
