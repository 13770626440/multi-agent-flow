"""
AgentProvisioner 单元测试

测试 Agent 动态供给机制：
1. 角色已存在（跳过创建）
2. 角色不存在（触发创建 + 发送入职包 + 配置 Cron）
3. 创建失败（异常处理）
4. 发送入职包失败（异常处理）
5. 配置 Cron 失败（异常处理）
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.agent_provisioner import AgentProvisioner


class TestAgentProvisioner:
    """AgentProvisioner 测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.provisioner = AgentProvisioner()

    @pytest.mark.asyncio
    async def test_role_exists_skip_creation(self):
        """测试：角色已存在，跳过创建"""
        with patch("app.core.agent_provisioner.openmoss_client", new_callable=AsyncMock) as mock_openmoss:
            mock_openmoss.list_agents.return_value = [
                {"role": "executor", "status": "active"},
                {"role": "reviewer", "status": "active"}
            ]

            result = await self.provisioner.ensure_role_exists("executor", "qwen3.6-plus")

            assert result is True
            mock_openmoss.list_agents.assert_called_once()

    @pytest.mark.asyncio
    async def test_role_not_exists_trigger_creation_and_cron(self):
        """测试：角色不存在，触发创建、入职和 Cron 配置"""
        with patch("app.core.agent_provisioner.openmoss_client", new_callable=AsyncMock) as mock_openmoss, \
             patch("app.core.agent_provisioner.openclaw_client", new_callable=AsyncMock) as mock_openclaw:
            
            mock_openmoss.list_agents.return_value = [{"role": "executor", "status": "active"}]
            mock_openmoss.get_prompt.return_value = "You are a reviewer..."
            mock_openmoss.get_tool_cli.return_value = "# CLI Content"

            result = await self.provisioner.ensure_role_exists("reviewer", "qwen3.6-plus")

            assert result is True
            
            # 验证创建 Agent
            mock_openclaw.create_agent.assert_called_once_with(
                name="reviewer-agent",
                model="qwen3.6-plus",
                workspace="/workspace/reviewer-agent"
            )
            
            # 验证发送入职包
            mock_openclaw.send_message_to_agent.assert_called_once()
            call_args = mock_openclaw.send_message_to_agent.call_args
            assert call_args[0][0] == "reviewer-agent"
            message_content = call_args[0][1]
            
            # 验证消息内容包含关键信息
            assert "reviewer" in message_content
            assert "You are a reviewer..." in message_content
            
            # 验证 Workspace 隔离规范
            assert "Workspace 使用规范" in message_content
            assert "/workspace/{task_id}/" in message_content
            assert "严禁在 `/workspace` 根目录" in message_content

            # 验证配置 Cron
            mock_openclaw.add_cron_job.assert_called_once()
            cron_call = mock_openclaw.add_cron_job.call_args
            assert cron_call[1]["cron_id"] == "reviewer-poll"
            assert cron_call[1]["agent_name"] == "reviewer-agent"

    @pytest.mark.asyncio
    async def test_create_agent_failure(self):
        """测试：创建 Agent 失败"""
        with patch("app.core.agent_provisioner.openmoss_client", new_callable=AsyncMock) as mock_openmoss, \
             patch("app.core.agent_provisioner.openclaw_client", new_callable=AsyncMock) as mock_openclaw:
            
            mock_openmoss.list_agents.return_value = []
            mock_openclaw.create_agent.side_effect = Exception("API Error")

            result = await self.provisioner.ensure_role_exists("patrol", "qwen3.5-plus")

            assert result is False
            mock_openclaw.send_message_to_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_onboarding_failure(self):
        """测试：发送入职包失败"""
        with patch("app.core.agent_provisioner.openmoss_client", new_callable=AsyncMock) as mock_openmoss, \
             patch("app.core.agent_provisioner.openclaw_client", new_callable=AsyncMock) as mock_openclaw:
            
            mock_openmoss.list_agents.return_value = []
            mock_openclaw.create_agent.return_value = {}
            mock_openclaw.send_message_to_agent.side_effect = Exception("Send Error")

            result = await self.provisioner.ensure_role_exists("tech-lead", "qwen3.6-plus")

            assert result is False
            mock_openclaw.add_cron_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_configure_cron_failure(self):
        """测试：配置 Cron 失败"""
        with patch("app.core.agent_provisioner.openmoss_client", new_callable=AsyncMock) as mock_openmoss, \
             patch("app.core.agent_provisioner.openclaw_client", new_callable=AsyncMock) as mock_openclaw:
            
            mock_openmoss.list_agents.return_value = []
            mock_openclaw.create_agent.return_value = {}
            mock_openclaw.send_message_to_agent.return_value = {}
            mock_openclaw.add_cron_job.side_effect = Exception("Cron Error")

            result = await self.provisioner.ensure_role_exists("executor", "qwen3.6-plus")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_agent_exists_error_handling(self):
        """测试：检查 Agent 存在性时发生错误"""
        with patch("app.core.agent_provisioner.openmoss_client", new_callable=AsyncMock) as mock_openmoss:
            mock_openmoss.list_agents.side_effect = Exception("Network Error")

            result = await self.provisioner.check_agent_exists("executor")

            # 应该返回 False 而不是抛出异常
            assert result is False
