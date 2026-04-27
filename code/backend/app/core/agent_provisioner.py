"""
AgentProvisioner - Agent 动态供给与入职管理

职责：
1. 在加载模板时，探测并创建缺失的 Agent 角色。
2. 自动发送"入职包"给新创建的 Agent，使其完成自我注册。
3. 配置 Agent 的 Cron 定时唤醒任务。
4. 根据角色动态加载 Skills 并注入到入职包。
"""
import logging
from typing import Dict, Any, List

from app.clients.openclaw_client import openclaw_client
from app.clients.openmoss_client import openmoss_client
from app.config import get_settings

# P0-2: 直接导入 loader.py（消除动态导入）
import importlib.util
import os
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_loader_path = os.path.join(_backend_dir, 'skills', 'agency-agent', 'loader.py')
_spec = importlib.util.spec_from_file_location("skill_loader", _loader_path)
_loader_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_loader_module)
create_skill_loader = _loader_module.create_skill_loader

logger = logging.getLogger(__name__)
settings = get_settings()

# 默认 Cron 配置
DEFAULT_CRON_CONFIGS = {
    "executor": {"schedule": "*/10 * * * *", "message": "Wake up and execute assigned tasks."},
    "reviewer": {"schedule": "*/15 * * * *", "message": "Wake up and review submitted tasks."},
    "patrol": {"schedule": "*/30 * * * *", "message": "Wake up and patrol system health."},
    "planner": {"schedule": "*/20 * * * *", "message": "Wake up and plan new tasks."},
    "tech-lead": {"schedule": "*/20 * * * *", "message": "Wake up and decompose complex tasks."},
}


class AgentProvisioner:
    """Agent 动态供给器"""

    async def ensure_role_exists(self, role_name: str, model: str) -> bool:
        """
        确保角色对应的 Agent 存在，不存在则创建、发送入职包并配置 Cron。
        """
        agent_name = f"{role_name}-agent"
        
        # 1. 检查 Agent 是否已注册
        if await self.check_agent_exists(role_name):
            logger.info(f"Agent for role '{role_name}' already exists.")
            return True
        
        # 2. 创建 Agent
        try:
            await self.create_agent(agent_name, model)
        except Exception as e:
            logger.error(f"Failed to create agent {agent_name}: {e}")
            return False
            
        # 3. 发送入职包
        try:
            await self.send_onboarding_package(agent_name, role_name)
            logger.info(f"Onboarding package sent to {agent_name}.")
        except Exception as e:
            logger.error(f"Failed to send onboarding package to {agent_name}: {e}")
            return False

        # 4. 配置 Cron
        try:
            await self.configure_cron(agent_name, role_name)
            logger.info(f"Cron configured for {agent_name}.")
            return True
        except Exception as e:
            logger.error(f"Failed to configure cron for {agent_name}: {e}")
            return False

    async def check_agent_exists(self, role_name: str) -> bool:
        """检查 OpenMOSS 中是否已注册该角色的 Agent。"""
        try:
            agents = await openmoss_client.list_agents()
            for agent in agents:
                if agent.get("role") == role_name and agent.get("status") == "active":
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking agent existence: {e}")
            return False

    async def create_agent(self, agent_name: str, model: str) -> None:
        """调用 OpenClaw API 创建 Agent。"""
        workspace = f"/workspace/{agent_name}"
        await openclaw_client.create_agent(
            name=agent_name,
            model=model,
            workspace=workspace
        )

    async def send_onboarding_package(self, agent_name: str, role_name: str) -> None:
        """
        获取入职包并发送给 Agent。
        入职包包含：提示词、task-cli.py、注册指引、角色对应的 Skills。
        """
        # 1. 获取入职包各组件
        prompt = await self._get_prompt(role_name)
        cli_tool = await self._get_cli_tool()
        reg_token = self._get_registration_token()
        skills_section = self._load_skills_for_role(role_name)

        # 2. 组装并发送消息
        message = self._build_onboarding_message(
            role_name=role_name,
            prompt=prompt,
            skills_section=skills_section,
            cli_tool=cli_tool,
            reg_token=reg_token
        )
        await openclaw_client.send_message_to_agent(agent_name, message)

    async def _get_prompt(self, role_name: str) -> str:
        """获取角色提示词"""
        prompt = await openmoss_client.get_prompt(role_name)
        return prompt or ""

    async def _get_cli_tool(self) -> str:
        """获取 CLI 工具内容"""
        cli_tool = await openmoss_client.get_tool_cli()
        return cli_tool or ""

    def _get_registration_token(self) -> str:
        """获取注册令牌"""
        return settings.OPENMOSS_REGISTRATION_TOKEN

    def _load_skills_for_role(self, role_name: str) -> str:
        """
        加载角色对应的 Skills 并格式化为 Markdown
        
        Args:
            role_name: 角色名称
        
        Returns:
            格式化的 Skills 内容
        """
        skill_loader = create_skill_loader(
            skills_dir=settings.SKILLS_DIR,
            role_skill_map=settings.DEFAULT_ROLE_SKILL_MAP
        )
        loaded_skills = skill_loader.load_skills_for_role(role_name)
        
        if not loaded_skills:
            logger.warning(f"No skills loaded for role '{role_name}'")
            return ""
        
        skills_parts = []
        for skill in loaded_skills:
            skills_parts.append(f"\n## Active Skill: {skill['name']}\n")
            skills_parts.append(skill['content'])
        
        logger.info(
            f"Loaded {len(loaded_skills)} skills for role '{role_name}': "
            f"{[s['name'] for s in loaded_skills]}"
        )
        
        return "\n\n## 角色能力 (Skills)\n" + "\n".join(skills_parts)

    def _build_onboarding_message(
        self,
        role_name: str,
        prompt: str,
        skills_section: str,
        cli_tool: str,
        reg_token: str
    ) -> str:
        """
        组装入职消息
        
        Args:
            role_name: 角色名称
            prompt: 提示词
            skills_section: Skills 内容
            cli_tool: CLI 工具内容
            reg_token: 注册令牌
        
        Returns:
            完整的入职消息
        """
        return f"""
# 欢迎入职！

你是 **{role_name}** 角色。请执行以下步骤完成配置：

## 1. 更新提示词
请将以下内容保存为你的核心指令 (AGENTS.md)：

{prompt}

{skills_section}

## 2. 下载工具
请执行以下命令下载任务 CLI 工具：
```bash
# 这里应该是具体的下载命令或内容
{cli_tool}
```

## 3. 自动注册
请使用以下注册令牌调用 OpenMOSS API 注册自己：
Token: `{reg_token}`

## 4. ⚠️ Workspace 使用规范 (重要)
所有任务产出物必须保存在共享工作区 `/workspace` 下，并严格按照 **Task ID** 进行隔离：
- 收到任务后，**必须**进入 `/workspace/{{task_id}}/` 目录进行操作。
- 严禁在 `/workspace` 根目录或其他非 Task ID 目录下创建文件。
- 读取前置任务产出物时，也请前往对应的 `/workspace/{{task_id}}/` 目录。

完成注册后，你将获得 API Key 并开始工作。
"""

    async def configure_cron(self, agent_name: str, role_name: str) -> None:
        """
        为 Agent 配置 Cron 定时唤醒任务。
        """
        # 获取角色的 Cron 配置，如果没有则使用默认
        cron_config = DEFAULT_CRON_CONFIGS.get(role_name, {})
        schedule = cron_config.get("schedule", "*/15 * * * *")
        message = cron_config.get("message", "Wake up and check tasks.")

        cron_id = f"{role_name}-poll"
        
        await openclaw_client.add_cron_job(
            cron_id=cron_id,
            agent_name=agent_name,
            schedule=schedule,
            message=message
        )

# 全局单例
agent_provisioner = AgentProvisioner()
