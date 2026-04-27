"""
MVP-04-T03 集成测试：模板加载 -> Agent 创建与入职全流程

测试目标：
验证从模板加载触发 Agent 动态供给，到 OpenClaw Agent 创建、入职包发送、Cron 配置的完整链路。

测试策略：
使用 respx Mock 外部 API，但串联 Backend 核心逻辑。
记录所有交互日志，用于生成测试报告。
"""
import pytest
import respx
import httpx
import asyncio
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.core.template_loader import TemplateLoader
from app.core.agent_provisioner import agent_provisioner
from app.clients.openclaw_client import openclaw_client
from app.clients.openmoss_client import openmoss_client

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("integration_test")

# 测试数据
TEST_TEMPLATE_DATA = {
    "template_id": "test-integration-flow",
    "version": "1.0.0",
    "roles": {
        "security-auditor": {
            "model": "qwen3.6-plus",
            "description": "安全审计员"
        }
    },
    "tasks": []
}

class TestMVP04T03Integration:
    """MVP-04-T03 集成测试类"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_provisioning_flow(self):
        """测试完整流程：模板加载 -> 探测 -> 创建 -> 入职 -> Cron"""
        
        # Mock Token 验证
        with patch("app.core.token_manager.token_manager.get_token", return_value="test-token"), \
             patch("app.core.token_manager.token_manager.get_headers", return_value={"Authorization": "Bearer test-token"}):

            # 1. 准备 Mock
            # OpenMOSS: 检查 Agent (返回空，表示不存在)
            openmoss_list_route = respx.get("http://openmoss:6565/api/agents").mock(
                return_value=httpx.Response(200, json=[])
            )
            # OpenMOSS: 获取 Prompt
            openmoss_prompt_route = respx.get("http://openmoss:6565/api/prompts/security-auditor").mock(
                return_value=httpx.Response(200, json={"content": "You are a security auditor..."})
            )
            # OpenMOSS: 获取 CLI
            openmoss_cli_route = respx.get("http://openmoss:6565/api/tools/cli").mock(
                return_value=httpx.Response(200, json={"content": "#!/usr/bin/env python3..."})
            )
            
            # OpenClaw: 创建 Agent
            openclaw_create_route = respx.post("http://openclaw-gateway:18789/api/agents").mock(
                return_value=httpx.Response(200, json={"status": "created"})
            )
            # OpenClaw: 发送消息
            openclaw_msg_route = respx.post(url__startswith="http://openclaw-gateway:18789/api/agents/").mock(
                return_value=httpx.Response(200, json={"status": "sent"})
            )
            # OpenClaw: 添加 Cron
            openclaw_cron_route = respx.post("http://openclaw-gateway:18789/api/cron").mock(
                return_value=httpx.Response(200, json={"status": "scheduled"})
            )

            # 2. 执行逻辑
            # 直接调用 AgentProvisioner，模拟 TemplateLoader 触发后的行为
            result = await agent_provisioner.ensure_role_exists("security-auditor", "qwen3.6-plus")

            # 3. 验证结果
            assert result is True, "Provisioning should succeed"

            # 验证 OpenMOSS 检查
            assert openmoss_list_route.called, "Should check if agent exists"

            # 验证 OpenClaw 创建 Agent
            assert openclaw_create_route.called, "Should create agent in OpenClaw"
            create_req = openclaw_create_route.calls[0].request
            import json
            create_json = json.loads(create_req.content)
            assert create_json["name"] == "security-auditor-agent"
            assert create_json["model"] == "qwen3.6-plus"
            assert create_json["workspace"] == "/workspace/security-auditor-agent"

            # 验证 OpenMOSS 获取入职素材
            assert openmoss_prompt_route.called, "Should fetch prompt"
            assert openmoss_cli_route.called, "Should fetch CLI tool"

            # 验证 OpenClaw 发送消息
            assert openclaw_msg_route.called, "Should send onboarding message"
            msg_req = openclaw_msg_route.calls[0].request
            msg_json = json.loads(msg_req.content)
            assert "security-auditor-agent" in msg_req.url.path
            assert "security-auditor" in msg_json["content"]
            assert "You are a security auditor..." in msg_json["content"]

            # 验证 OpenClaw 配置 Cron
            assert openclaw_cron_route.called, "Should configure cron job"
            cron_req = openclaw_cron_route.calls[0].request
            cron_json = json.loads(cron_req.content)
            assert cron_json["id"] == "security-auditor-poll"
            assert cron_json["agent"] == "security-auditor-agent"
            assert "schedule" in cron_json

            # 4. 生成测试报告数据
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "result": "PASS",
                "requests": [
                    {"service": "OpenMOSS", "method": "GET", "path": "/api/agents", "status": 200},
                    {"service": "OpenClaw", "method": "POST", "path": "/api/agents", "status": 200, "payload": create_json},
                    {"service": "OpenMOSS", "method": "GET", "path": "/api/prompts/security-auditor", "status": 200},
                    {"service": "OpenMOSS", "method": "GET", "path": "/api/tools/cli", "status": 200},
                    {"service": "OpenClaw", "method": "POST", "path": "/api/agents/.../message", "status": 200, "payload": msg_json},
                    {"service": "OpenClaw", "method": "POST", "path": "/api/cron", "status": 200, "payload": cron_json}
                ]
            }
            
            # 保存到文件 (模拟日志记录)
            import json
            with open("test/integration_report_mvp04_t03.json", "w") as f:
                json.dump(report_data, f, indent=2)
