"""
OpenClawClient 超时保护单元测试

覆盖：
1. CLI 正常执行
2. CLI 超时保护
3. CLI 异常处理
"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.clients.openclaw_client import OpenClawClient, CLI_TIMEOUT


@pytest.fixture
def client():
    return OpenClawClient()


# ── 测试 1: CLI 正常执行 ─────────────────────────────────────

@pytest.mark.asyncio
async def test_cli_success(client):
    """CLI 正常执行应返回成功"""
    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"output", b""))

    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        result = await client._exec_cli(["echo", "hello"])

    assert result["status"] == "success"
    assert result["output"] == "output"


# ── 测试 2: CLI 超时保护 ─────────────────────────────────────

@pytest.mark.asyncio
async def test_cli_timeout(client):
    """CLI 超时应被捕获并返回错误"""
    mock_proc = AsyncMock()
    mock_proc.kill = MagicMock()

    async def slow_communicate():
        await asyncio.sleep(100)

    mock_proc.communicate = slow_communicate

    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        result = await client._exec_cli(["sleep", "100"], timeout=0.1)

    assert result["status"] == "error"
    assert "timed out" in result["error"]
    mock_proc.kill.assert_called_once()


# ── 测试 3: CLI 非零返回码 ───────────────────────────────────

@pytest.mark.asyncio
async def test_cli_error_return(client):
    """CLI 返回非零应返回错误"""
    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"Error: not found"))

    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        result = await client._exec_cli(["openclaw", "agents", "list"])

    assert result["status"] == "error"
    assert "not found" in result["error"]


# ── 测试 4: CLI 异常 ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_cli_exception(client):
    """CLI 执行异常应被捕获"""
    with patch('asyncio.create_subprocess_exec', side_effect=OSError("docker not found")):
        result = await client._exec_cli(["docker", "exec"])

    assert result["status"] == "exception"
    assert "docker not found" in result["error"]


# ── 测试 5: list_agents 解析 ─────────────────────────────────

@pytest.mark.asyncio
async def test_list_agents_parsing(client):
    """应正确解析 agent 列表"""
    mock_output = """Agents:
- main (default)
  Workspace: ~/.openclaw/workspace
- test-agent
  Workspace: /workspace/test-agent
"""
    with patch.object(client, '_exec_cli', return_value={"status": "success", "output": mock_output}):
        agents = await client.list_agents()

    assert "main" in agents
    assert "test-agent" in agents


@pytest.mark.asyncio
async def test_list_agents_cli_failure(client):
    """CLI 失败应返回空列表"""
    with patch.object(client, '_exec_cli', return_value={"status": "error", "error": "failed"}):
        agents = await client.list_agents()

    assert agents == []


# ── 测试 6: send_message_to_agent ────────────────────────────

@pytest.mark.asyncio
async def test_send_message_timeout(client):
    """发送消息超时应返回错误"""
    async def slow_communicate():
        await asyncio.sleep(100)

    mock_proc = AsyncMock()
    mock_proc.kill = MagicMock()
    mock_proc.communicate = slow_communicate

    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        result = await client.send_message_to_agent("nonexistent", "hello", )

    assert result["status"] == "error"
    assert "timed out" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
