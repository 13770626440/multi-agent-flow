"""
Decomposer 异步等待机制单元测试

测试异步等待机制的核心功能：
1. 正常完成通知
2. 超时处理
3. 任务失败通知
4. 并发等待
"""
import pytest
import asyncio
from app.core.decomposer import Decomposer, DecompositionFailed


class TestDecomposerAsync:
    """Decomposer 异步等待测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.decomposer = Decomposer(timeout=1)  # 1 秒超时，加快测试
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_normal(self):
        """TC-WAIT-01: 测试正常完成"""
        openmoss_id = "om_test_001"
        
        # 启动异步通知任务（0.1 秒后通知完成）
        async def notify_after_delay():
            await asyncio.sleep(0.1)
            self.decomposer.notify_completion(openmoss_id, {"output": "[{\"name\": \"task1\"}]"})
        
        asyncio.create_task(notify_after_delay())
        
        # 等待完成
        result = await self.decomposer._wait_for_completion(openmoss_id)
        
        assert result == {"output": "[{\"name\": \"task1\"}]"}
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self):
        """TC-WAIT-02: 测试超时"""
        openmoss_id = "om_test_002"
        
        # 不通知完成，等待超时
        with pytest.raises(DecompositionFailed, match="timeout after 1s"):
            await self.decomposer._wait_for_completion(openmoss_id)
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_failure(self):
        """TC-WAIT-03: 测试任务失败"""
        openmoss_id = "om_test_003"
        
        # 启动异步通知任务（0.1 秒后通知失败）
        async def notify_failure_after_delay():
            await asyncio.sleep(0.1)
            self.decomposer.notify_failure(openmoss_id, "Agent execution failed")
        
        asyncio.create_task(notify_failure_after_delay())
        
        # 等待完成（应抛出异常）
        with pytest.raises(DecompositionFailed, match="Agent execution failed"):
            await self.decomposer._wait_for_completion(openmoss_id)
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_concurrent(self):
        """TC-WAIT-04: 测试并发等待"""
        openmoss_id_1 = "om_test_004_1"
        openmoss_id_2 = "om_test_004_2"
        
        # 启动两个异步通知任务
        async def notify_both():
            await asyncio.sleep(0.1)
            self.decomposer.notify_completion(openmoss_id_1, {"output": "[task1]"})
            self.decomposer.notify_completion(openmoss_id_2, {"output": "[task2]"})
        
        asyncio.create_task(notify_both())
        
        # 并发等待两个任务
        result1, result2 = await asyncio.gather(
            self.decomposer._wait_for_completion(openmoss_id_1),
            self.decomposer._wait_for_completion(openmoss_id_2)
        )
        
        assert result1 == {"output": "[task1]"}
        assert result2 == {"output": "[task2]"}
    
    @pytest.mark.asyncio
    async def test_notify_completion_without_waiter(self):
        """TC-WAIT-05: 测试无等待者时通知完成"""
        openmoss_id = "om_test_005"
        
        # 直接通知完成（无等待者）
        self.decomposer.notify_completion(openmoss_id, {"output": "[task1]"})
        
        # 结果应已保存
        assert self.decomposer.completion_results[openmoss_id] == {"output": "[task1]"}
