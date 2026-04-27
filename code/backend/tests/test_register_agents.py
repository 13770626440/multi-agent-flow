"""
Agent 注册脚本单元测试

测试策略：
- 使用 respx Mock OpenMOSS API
- 测试正常注册、已存在、重试、dry-run 等场景
"""
import pytest
import respx
import httpx
import asyncio
from unittest.mock import patch, MagicMock
from scripts.register_agents import register_agent


class TestAgentRegistration:
    """Agent 注册测试类"""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_register_agent_success(self):
        """TC-REG-01: 正常注册"""
        respx.post("http://openmoss:6565/api/agents/register").mock(
            return_value=httpx.Response(200, json={
                "id": "agent_001",
                "name": "planner-001",
                "role": "planner",
                "api_key": "sk_planner_xxx"
            })
        )
        
        result = await register_agent("planner-001", "planner", "Test planner")
        
        assert result["id"] == "agent_001"
        assert result["api_key"] == "sk_planner_xxx"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_register_agent_already_exists(self):
        """TC-REG-02: Agent 已存在"""
        respx.post("http://openmoss:6565/api/agents/register").mock(
            return_value=httpx.Response(400, json={"detail": "Agent already exists"})
        )
        
        result = await register_agent("planner-001", "planner", "Test planner")
        
        # 应返回空或已存在的 Agent
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_register_agent_retry(self):
        """TC-REG-03: 注册失败重试"""
        call_count = [0]
        
        def mock_register(request):
            call_count[0] += 1
            if call_count[0] < 3:
                return httpx.Response(500, json={"error": "Internal error"})
            return httpx.Response(200, json={
                "id": "agent_003",
                "name": "executor-001",
                "role": "executor",
                "api_key": "sk_executor_xxx"
            })
        
        respx.post("http://openmoss:6565/api/agents/register").mock(side_effect=mock_register)
        
        result = await register_agent("executor-001", "executor", "Test executor")
        
        assert call_count[0] == 3
        assert result["api_key"] == "sk_executor_xxx"
    

