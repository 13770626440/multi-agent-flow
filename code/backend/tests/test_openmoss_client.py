"""
OpenMOSSClient 完整单元测试

测试覆盖：
1. API 调用正确性 (URL, Method, Headers, Payload)
2. Token 角色分配正确性
3. 重试机制有效性 (网络错误重试，业务错误不重试)
4. 快捷方法封装
"""
import pytest
import httpx
import os
from unittest.mock import AsyncMock, patch, MagicMock
from tenacity import RetryError

from app.clients.openmoss_client import OpenMOSSClient
from app.core.token_manager import token_manager


class TestOpenMOSSClient:
    """OpenMOSSClient 单元测试"""

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

    @pytest.fixture
    def client(self):
        return OpenMOSSClient()

    def _mock_response(self, json_data, status_code=200):
        """辅助函数：创建 Mock 响应对象"""
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @pytest.mark.asyncio
    async def test_create_sub_task(self, client):
        """测试创建子任务 (Planner)"""
        mock_resp = self._mock_response({"id": "sub_001", "status": "pending"})
        
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            
            result = await client.create_sub_task(
                task_id="task_001",
                name="Test Task",
                assigned_agent="executor_001",
                description="Desc",
                acceptance="Acc"
            )
            
            assert result["id"] == "sub_001"
            
            # 验证请求参数
            # httpx.AsyncClient.request(method, url, ...)
            # args[0] is method, args[1] is url
            call_args = mock_req.call_args
            assert call_args.args[0] == "POST"
            assert "sub-tasks" in call_args.args[1]
            assert call_args.kwargs["json"]["task_id"] == "task_001"
            assert call_args.kwargs["json"]["name"] == "Test Task"
            # 验证使用了 Planner Token
            assert call_args.kwargs["headers"]["X-Agent-Key"] == "test_planner_key"

    @pytest.mark.asyncio
    async def test_get_sub_task(self, client):
        """测试获取子任务详情 (Planner)"""
        mock_resp = self._mock_response({"id": "sub_001", "name": "Task 1"})
        
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            
            result = await client.get_sub_task("sub_001")
            
            assert result["name"] == "Task 1"
            call_args = mock_req.call_args
            assert call_args.args[0] == "GET"
            assert "sub_001" in call_args.args[1]

    @pytest.mark.asyncio
    async def test_list_sub_tasks_with_filters(self, client):
        """测试查询子任务列表 (Planner)"""
        mock_resp = self._mock_response({"items": [{"id": "1"}, {"id": "2"}]})
        
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            
            result = await client.list_sub_tasks(task_id="task_001", status="pending")
            
            assert len(result) == 2
            call_args = mock_req.call_args
            assert call_args.kwargs["params"]["task_id"] == "task_001"
            assert call_args.kwargs["params"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_submit_sub_task(self, client):
        """测试提交子任务 (Executor)"""
        mock_resp = self._mock_response({"status": "review"})
        
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            
            await client.submit_sub_task("sub_001", "session_123")
            
            call_args = mock_req.call_args
            assert "submit" in call_args.args[1]
            assert call_args.kwargs["json"]["session_id"] == "session_123"
            # 验证使用了 Executor Token
            assert call_args.kwargs["headers"]["X-Agent-Key"] == "test_executor_key"

    @pytest.mark.asyncio
    async def test_block_sub_task(self, client):
        """测试阻塞子任务 (Patrol)"""
        mock_resp = self._mock_response({"status": "blocked"})
        
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            
            await client.block_sub_task("sub_001")
            
            call_args = mock_req.call_args
            assert "block" in call_args.args[1]
            # 验证使用了 Patrol Token
            assert call_args.kwargs["headers"]["X-Agent-Key"] == "test_patrol_key"

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, client):
        """测试网络错误时的重试机制"""
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            # 模拟持续的网络连接错误
            mock_req.side_effect = httpx.ConnectError("Connection refused")
            
            # tenacity reraise=True 会抛出原始异常
            with pytest.raises(httpx.ConnectError):
                await client.get_sub_task("sub_001")
            
            # 验证重试了 3 次 (stop_after_attempt(3))
            assert mock_req.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_http_error(self, client):
        """测试 HTTP 错误 (如 404) 不触发重试"""
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            # 模拟 404 错误
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("Not Found", request=None, response=mock_resp)
            mock_req.return_value = mock_resp
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_sub_task("sub_001")
            
            # 验证没有重试，只调用了一次
            assert mock_req.call_count == 1
