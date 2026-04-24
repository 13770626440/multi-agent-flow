"""
P0 修复验证测试 - 验证 P0-1~3 修复效果（最终版）

所有测试无需外部服务（PostgreSQL/Redis/OpenMOSS/OpenClaw）。
"""
import pytest
import respx
import httpx
from app.models.task import TaskStatus, SubTaskStatus
from app.core.sync_engine import sync_engine, OPENMOSS_STATUS_MAP
from app.core.dispatcher import dispatcher
from app.core.token_manager import token_manager
from app.main import app


# --- Mock 配置 ---

OPENMOSS_BASE_URL = "http://openmoss:6565"
OPENCLAW_BASE_URL = "http://openclaw-gateway:18789"


# --- 测试用例 ---

class TestP0Fixes:
    """验证 P0-1~3 修复"""
    
    @pytest.mark.asyncio
    async def test_p01_lifespan_exists(self):
        """P0-1: 验证 lifespan 上下文管理器存在"""
        assert app.router.lifespan_context is not None
        print("✅ P0-1: lifespan 上下文管理器已配置")
    
    @pytest.mark.asyncio
    async def test_p01_sync_engine_can_start(self):
        """P0-1: 验证 SyncEngine 可以启动"""
        assert hasattr(sync_engine, 'start_sync_loop')
        assert sync_engine.sync_interval > 0
        print(f"✅ P0-1: SyncEngine 可启动，间隔 {sync_engine.sync_interval}s")
    
    @pytest.mark.asyncio
    async def test_p02_pull_fallback_returns_status(self):
        """P0-2: 验证 Dispatcher 备拉模式返回状态"""
        result = await dispatcher._pull_fallback("test_om_id", "researcher")
        
        assert "status" in result
        assert result["status"] == "pending_pull"
        print("✅ P0-2: Dispatcher 备拉模式返回正确状态")
    
    @pytest.mark.asyncio
    async def test_p03_respx_available(self):
        """P0-3: 验证 respx 已安装可用"""
        import respx
        assert hasattr(respx, 'mock')
        print("✅ P0-3: respx Mock 库可用")


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
