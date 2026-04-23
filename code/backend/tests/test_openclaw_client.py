"""
OpenClawClient 单元测试

测试覆盖：
1. 接口调用正确性 (URL, Method, Headers)
2. 网络异常重试机制 (tenacity)
3. 业务异常处理 (404 不重试)
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from tenacity import RetryError

from app.clients.openclaw_client import OpenClawClient
from app.core.token_manager import token_manager


class TestOpenClawClient:
    """OpenClawClient 单元测试"""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """确保测试环境中存在 Token"""
        token_manager._tokens.update({
            "gateway": "test_gateway_key",
        })

    @pytest.fixture
    def client(self):
        return OpenClawClient()

    def _mock_response(self, json_data, status_code=200):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @pytest.mark.asyncio
    async def test_get_conversation_success(self, client):
        """测试获取会话详情 (正常情况)"""
        mock_resp = self._mock_response({"id": "conv_1", "messages": []})
        
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            
            result = await client.get_conversation("conv_1")
            
            assert result["id"] == "conv_1"
            call_args = mock_req.call_args
            # method 和 url 都是位置参数
            assert call_args.args[0] == "GET"
            assert "conv_1" in call_args.args[1]
            # 验证 Token 注入 (headers 是关键字参数)
            assert "Authorization" in call_args.kwargs.get("headers", {})

    @pytest.mark.asyncio
    async def test_list_conversations_params(self, client):
        """测试列表查询参数传递"""
        mock_resp = self._mock_response({"items": []})
        
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            
            await client.list_conversations(limit=10, offset=5)
            
            call_args = mock_req.call_args
            assert call_args.kwargs["params"]["limit"] == 10
            assert call_args.kwargs["params"]["offset"] == 5

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, client):
        """测试网络错误时的重试机制"""
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = httpx.ConnectError("Connection refused")
            
            with pytest.raises(httpx.ConnectError):
                await client.get_conversation("conv_1")
            
            # 验证重试了 3 次
            assert mock_req.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_404(self, client):
        """测试 404 错误不触发重试"""
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("Not Found", request=None, response=mock_resp)
            mock_req.return_value = mock_resp
            
            result = await client.get_conversation("conv_999")
            
            assert result == {} # 应该返回空字典
            assert mock_req.call_count == 1 # 只调用了一次，没有重试
