"""
SyncEngine 动态任务处理单元测试

测试动态分解任务完成后的处理逻辑：
1. 正常完成通知
2. 获取 OpenMOSS 输出
3. 异常处理
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.sync_engine import SyncEngine
from app.models.task import SubTaskRecord, SubTaskStatus


class TestSyncEngineDecomposition:
    """SyncEngine 动态任务处理测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.sync_engine = SyncEngine()
    
    @pytest.mark.asyncio
    async def test_handle_decomposition_complete_normal(self):
        """TC-SYNC-01: 测试正常完成通知"""
        # 创建模拟子任务
        sub_task = MagicMock(spec=SubTaskRecord)
        sub_task.id = "sub_001"
        sub_task.openmoss_id = "om_decompose_001"
        sub_task.is_decomposition_task = True
        sub_task.decomposition_output = None
        
        om_status = {
            "status": "done",
            "output": '[{"name": "task1", "role": "backend"}]'
        }
        
        # Mock session（不需要实际数据库操作）
        session = AsyncMock()
        
        # 调用处理方法
        await self.sync_engine._handle_decomposition_complete(
            session, sub_task, om_status
        )
        
        # 验证 decomposition_output 已保存
        assert sub_task.decomposition_output == '[{"name": "task1", "role": "backend"}]'
        
        # 验证 Decomposer 收到通知
        assert "om_decompose_001" in self.sync_engine.decomposer.completion_results
    
    @pytest.mark.asyncio
    async def test_handle_decomposition_complete_no_output(self):
        """TC-SYNC-02: 测试无输出情况"""
        sub_task = MagicMock(spec=SubTaskRecord)
        sub_task.id = "sub_002"
        sub_task.openmoss_id = "om_decompose_002"
        sub_task.is_decomposition_task = True
        sub_task.decomposition_output = None
        
        om_status = {
            "status": "done",
            "deliverable": '[{"name": "task2"}]'
        }
        
        session = AsyncMock()
        
        await self.sync_engine._handle_decomposition_complete(
            session, sub_task, om_status
        )
        
        # 验证使用 deliverable 字段
        assert sub_task.decomposition_output == '[{"name": "task2"}]'
    
    @pytest.mark.asyncio
    async def test_handle_decomposition_complete_error(self):
        """TC-SYNC-03: 测试异常处理"""
        sub_task = MagicMock(spec=SubTaskRecord)
        sub_task.id = "sub_003"
        sub_task.openmoss_id = "om_decompose_003"
        sub_task.is_decomposition_task = True
        sub_task.decomposition_output = None
        
        session = AsyncMock()
        
        # 模拟 notify_completion 抛出异常
        # notify_failure 内部也会调用 notify_completion，所以需要让第二次调用成功
        call_count = [0]
        def mock_notify(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Test error")
            return None
        
        with patch.object(
            self.sync_engine.decomposer,
            'notify_completion',
            side_effect=mock_notify
        ):
            # 不应抛出异常，而是记录错误
            await self.sync_engine._handle_decomposition_complete(
                session, sub_task, {"status": "done"}
            )
            
            # 验证 notify_completion 被调用了 2 次（第一次失败，第二次通过 notify_failure）
            assert call_count[0] == 2
