"""
SyncEngine + Decomposer 集成测试

测试完整的动态任务分解流程：
1. SyncEngine 检测到动态任务完成
2. 获取输出并通知 Decomposer
3. Decomposer 解析 JSON 并创建后续子任务
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.sync_engine import SyncEngine
from app.core.decomposer import Decomposer
from app.models.task import SubTaskRecord, SubTaskStatus


class TestSyncEngineDecomposerIntegration:
    """SyncEngine + Decomposer 集成测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.sync_engine = SyncEngine()
    
    @pytest.mark.asyncio
    async def test_full_decomposition_flow(self):
        """TC-INT-01: 测试完整分解流程"""
        # 1. 创建模拟子任务
        sub_task = MagicMock(spec=SubTaskRecord)
        sub_task.id = "sub_decompose_001"
        sub_task.openmoss_id = "om_decompose_001"
        sub_task.is_decomposition_task = True
        sub_task.decomposition_output = None
        sub_task.instance_id = "task_001"
        
        om_status = {
            "status": "done",
            "output": '[{"name": "task1", "role": "backend", "dependencies": []}]'
        }
        
        session = AsyncMock()
        
        # 2. 调用处理方法
        await self.sync_engine._handle_decomposition_complete(
            session, sub_task, om_status
        )
        
        # 3. 验证 decomposition_output 已保存
        assert sub_task.decomposition_output == '[{"name": "task1", "role": "backend", "dependencies": []}]'
        
        # 4. 验证 Decomposer 收到通知
        assert "om_decompose_001" in self.sync_engine.decomposer.completion_results
        
        result = self.sync_engine.decomposer.completion_results["om_decompose_001"]
        assert result["output"] == '[{"name": "task1", "role": "backend", "dependencies": []}]'
    
    @pytest.mark.asyncio
    async def test_decomposition_with_deliverable_field(self):
        """TC-INT-02: 测试使用 deliverable 字段"""
        sub_task = MagicMock(spec=SubTaskRecord)
        sub_task.id = "sub_decompose_002"
        sub_task.openmoss_id = "om_decompose_002"
        sub_task.is_decomposition_task = True
        sub_task.decomposition_output = None
        
        # OpenMOSS 返回 deliverable 而不是 output
        om_status = {
            "status": "done",
            "deliverable": '[{"name": "task2", "role": "frontend"}]'
        }
        
        session = AsyncMock()
        
        await self.sync_engine._handle_decomposition_complete(
            session, sub_task, om_status
        )
        
        # 验证使用 deliverable 字段
        assert sub_task.decomposition_output == '[{"name": "task2", "role": "frontend"}]'
    
    @pytest.mark.asyncio
    async def test_decomposition_with_result_field(self):
        """TC-INT-03: 测试使用 result 字段"""
        sub_task = MagicMock(spec=SubTaskRecord)
        sub_task.id = "sub_decompose_003"
        sub_task.openmoss_id = "om_decompose_003"
        sub_task.is_decomposition_task = True
        sub_task.decomposition_output = None
        
        om_status = {
            "status": "done",
            "result": '[{"name": "task3", "role": "database"}]'
        }
        
        session = AsyncMock()
        
        await self.sync_engine._handle_decomposition_complete(
            session, sub_task, om_status
        )
        
        # 验证使用 result 字段
        assert sub_task.decomposition_output == '[{"name": "task3", "role": "database"}]'
    
    @pytest.mark.asyncio
    async def test_decomposition_empty_output(self):
        """TC-INT-04: 测试空输出情况"""
        sub_task = MagicMock(spec=SubTaskRecord)
        sub_task.id = "sub_decompose_004"
        sub_task.openmoss_id = "om_decompose_004"
        sub_task.is_decomposition_task = True
        sub_task.decomposition_output = None
        
        om_status = {
            "status": "done"
        }
        
        session = AsyncMock()
        
        await self.sync_engine._handle_decomposition_complete(
            session, sub_task, om_status
        )
        
        # 验证输出为空字符串
        assert sub_task.decomposition_output == ""
