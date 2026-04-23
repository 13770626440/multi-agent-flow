"""
MVP-02-T03 任务管理模块单元测试

测试覆盖：
1. TokenManager 凭证管理
2. DAGEngine 依赖管理
3. Dispatcher 派发逻辑
4. ErrorHandler 重试机制
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.token_manager import TokenManager, token_manager
from app.core.dag_engine import DAGEngine
from app.core.dispatcher import Dispatcher
from app.core.error_handler import ErrorHandler


class TestTokenManager:
    """TokenManager 单元测试"""
    
    def test_get_valid_token(self):
        """测试获取有效 Token"""
        with patch.dict('os.environ', {'OPENMOSS_PLANNER_TOKEN': 'test_planner'}):
            tm = TokenManager()
            assert tm.get_token('planner') == 'test_planner'
    
    def test_get_invalid_role(self):
        """测试获取无效角色"""
        tm = TokenManager()
        with pytest.raises(ValueError, match="Invalid role"):
            tm.get_token('invalid_role')
    
    def test_get_headers_agent(self):
        """测试获取 Agent 请求头"""
        with patch.dict('os.environ', {'OPENMOSS_PLANNER_TOKEN': 'test_key'}):
            tm = TokenManager()
            headers = tm.get_headers('planner', 'agent')
            assert headers == {'X-Agent-Key': 'test_key'}
    
    def test_get_headers_gateway(self):
        """测试获取 Gateway 请求头"""
        with patch.dict('os.environ', {'OPENCLAW_GATEWAY_TOKEN': 'test_gw'}):
            tm = TokenManager()
            headers = tm.get_headers('gateway', 'gateway')
            assert headers == {'Authorization': 'Bearer test_gw'}
    
    @pytest.mark.asyncio
    async def test_refresh_token(self):
        """测试热更新 Token"""
        tm = TokenManager()
        await tm.refresh_token('planner', 'new_token')
        assert tm.get_token('planner') == 'new_token'
    
    def test_get_all_tokens_status(self):
        """测试获取所有 Token 状态"""
        tm = TokenManager()
        status = tm.get_all_tokens_status()
        assert isinstance(status, dict)
        assert 'planner' in status


class TestDAGEngine:
    """DAGEngine 单元测试"""
    
    def test_valid_dag(self):
        """测试有效 DAG 初始化"""
        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": ["t1"]},
            {"id": "t3", "dependencies": ["t2"]}
        ]
        engine = DAGEngine(tasks)
        order = engine.get_execution_order()
        assert order.index("t1") < order.index("t2") < order.index("t3")
    
    def test_circular_dependency(self):
        """测试循环依赖检测"""
        tasks = [
            {"id": "t1", "dependencies": ["t3"]},
            {"id": "t2", "dependencies": ["t1"]},
            {"id": "t3", "dependencies": ["t2"]}
        ]
        with pytest.raises(ValueError, match="Circular dependency"):
            DAGEngine(tasks)
    
    def test_get_ready_tasks(self):
        """测试获取就绪任务"""
        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": []},
            {"id": "t3", "dependencies": ["t1", "t2"]}
        ]
        engine = DAGEngine(tasks)
        
        # 初始状态：t1 和 t2 就绪
        ready = engine.get_ready_tasks(set())
        assert set(ready) == {"t1", "t2"}
        
        # t1 完成后：t2 仍就绪
        ready = engine.get_ready_tasks({"t1"})
        assert ready == ["t2"]
        
        # t1, t2 完成后：t3 就绪
        ready = engine.get_ready_tasks({"t1", "t2"})
        assert ready == ["t3"]
    
    def test_get_dependents(self):
        """测试获取后续任务"""
        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": ["t1"]},
            {"id": "t3", "dependencies": ["t1"]}
        ]
        engine = DAGEngine(tasks)
        dependents = engine.get_dependents("t1")
        assert set(dependents) == {"t2", "t3"}
    
    def test_to_dict_and_from_dict(self):
        """测试 DAG 序列化与反序列化"""
        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": ["t1"]}
        ]
        engine = DAGEngine(tasks)
        data = engine.to_dict()
        
        restored = DAGEngine.from_dict(data)
        assert restored.get_execution_order() == engine.get_execution_order()


class TestDispatcher:
    """Dispatcher 单元测试"""
    
    @pytest.mark.asyncio
    async def test_dispatch_push_success(self):
        """测试主推模式成功"""
        dispatcher = Dispatcher()
        with patch.object(dispatcher, '_push_to_openclaw', new_callable=AsyncMock) as mock_push:
            with patch.object(dispatcher, '_pull_fallback', new_callable=AsyncMock) as mock_pull:
                result = await dispatcher.dispatch_task(
                    sub_task_id="sub_001",
                    openmoss_id="om_001",
                    role="executor_db",
                    instruction="Test instruction"
                )
                assert result["status"] == "pushed"
                mock_push.assert_called_once()
                mock_pull.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_dispatch_push_fail_fallback(self):
        """测试主推失败降级为备拉"""
        dispatcher = Dispatcher()
        with patch.object(dispatcher, '_push_to_openclaw', side_effect=ConnectionError("API down")):
            with patch.object(dispatcher, '_pull_fallback', new_callable=AsyncMock) as mock_pull:
                result = await dispatcher.dispatch_task(
                    sub_task_id="sub_001",
                    openmoss_id="om_001",
                    role="executor_db",
                    instruction="Test instruction"
                )
                assert result["status"] == "pending_pull"
                mock_pull.assert_called_once()


class TestErrorHandler:
    """ErrorHandler 单元测试"""
    
    @pytest.mark.asyncio
    async def test_handle_task_failure_retry(self):
        """测试失败处理 - 重试"""
        handler = ErrorHandler()
        result = await handler.handle_task_failure("sub_001", Exception("Test error"), 1)
        assert result == "retry"
    
    @pytest.mark.asyncio
    async def test_handle_task_failure_blocked(self):
        """测试失败处理 - 超过重试上限"""
        handler = ErrorHandler()
        result = await handler.handle_task_failure("sub_001", Exception("Test error"), 3)
        assert result == "blocked"
