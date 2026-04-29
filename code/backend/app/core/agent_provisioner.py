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

# ARCH-006 修复：安全的 Skill Loader 导入
import importlib.util
from pathlib import Path
import os

def _safe_load_skill_loader():
    """
    安全加载 Skill Loader（ARCH-006 修复）
    验证路径在 SKILLS_DIR 范围内，防止路径遍历攻击
    """
    from app.config import get_settings
    settings = get_settings()
    skills_dir = Path(settings.SKILLS_DIR).resolve()
    
    # 尝试两种可能的路径
    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate_paths = [
        os.path.join(_backend_dir, 'skills', 'agency-agent', 'loader.py'),  # 本地开发
        os.path.join(os.path.dirname(_backend_dir), 'skills', 'agency-agent', 'loader.py')  # 容器内
    ]
    
    for _skills_path in candidate_paths:
        if os.path.exists(_skills_path):
            # ARCH-006 修复：验证路径在 skills_dir 范围内
            resolved_path = Path(_skills_path).resolve()
            try:
                resolved_path.relative_to(skills_dir)
            except ValueError:
                raise SecurityError(f"Skill loader path {_skills_path} is outside SKILLS_DIR {skills_dir}")
            
            _loader_path = _skills_path
            break
    else:
        raise FileNotFoundError(f"Skill loader not found in expected paths")
    
    _spec = importlib.util.spec_from_file_location("skill_loader", _loader_path)
    _loader_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_loader_module)
    return _loader_module.create_skill_loader

class SecurityError(Exception):
    pass

create_skill_loader = _safe_load_skill_loader()

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
        
        # 1. 检查 OpenClaw 中是否已存在该 Agent
        if await self.check_agent_exists_in_openclaw(agent_name):
            logger.info(f"Agent '{agent_name}' already exists in OpenClaw, sending onboarding package.")
            # Agent 已存在，但仍需发送入职包（可能更新了 prompt/skills）
            try:
                await self.send_onboarding_package(agent_name, role_name)
                logger.info(f"Onboarding package sent to {agent_name}.")
            except Exception as e:
                logger.error(f"Failed to send onboarding package to {agent_name}: {e}")
                return False
            
            # 配置 Cron（如果已存在可能不需要，但确保配置正确）
            try:
                await self.configure_cron(agent_name, role_name)
                logger.info(f"Cron configured for {agent_name}.")
                return True
            except Exception as e:
                logger.error(f"Failed to configure cron for {agent_name}: {e}")
                return False
        
        # 2. 创建 Agent
        try:
            result = await self.create_agent(agent_name, model)
            if result.get("status") == "error":
                # 如果是因为已存在，继续后续步骤
                if "already exists" in result.get("error", ""):
                    logger.info(f"Agent '{agent_name}' already exists, proceeding with onboarding.")
                else:
                    logger.error(f"Failed to create agent {agent_name}: {result.get('error')}")
                    return False
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

    async def check_agent_exists_in_openclaw(self, agent_name: str) -> bool:
        """检查 OpenClaw 中是否已存在该 Agent。"""
        try:
            agents = await openclaw_client.list_agents()
            return agent_name in agents
        except Exception as e:
            logger.warning(f"Error checking agent existence in OpenClaw: {e}")
            return False

    async def create_agent(self, agent_name: str, model: str) -> Dict[str, Any]:
        """调用 OpenClaw API 创建 Agent。"""
        workspace = f"/workspace/{agent_name}"
        return await openclaw_client.create_agent(
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
        return f"""# 欢迎入职！

你是 **{role_name}** 角色。请立即执行以下操作：

## 第一步：保存核心指令

**你必须立即将以下内容写入 `/workspace/{role_name}-agent/AGENTS.md` 文件：**

```markdown
# {role_name}

{prompt}

{skills_section}

## ⚠️ Workspace 使用规范
所有任务产出物必须保存在共享工作区 `/workspace` 下，并严格按照 **Task ID** 进行隔离：
- 收到任务后，**必须**进入 `/workspace/{{task_id}}/` 目录进行操作。
- 严禁在 `/workspace` 根目录或其他非 Task ID 目录下创建文件。
- 读取前置任务产出物时，也请前往对应的 `/workspace/{{task_id}}/` 目录。

## 📚 Skills 路径说明
Skills 已预装在 `/app/skills/` 目录下：
- `/app/skills/agency-agent/SKILL.md` - 基座 Skill（任务解析和执行）
- `/app/skills/multi-agent-flow-manager/SKILL.md` - 任务管理 Skill

加载 Skill 时，请使用绝对路径 `/app/skills/{{skill_name}}/SKILL.md`
```

**请立即使用 write 工具将上述内容保存到 AGENTS.md！**

## 第二步：注册到 OpenMOSS

使用以下注册令牌调用 OpenMOSS API 注册自己：
Token: `{reg_token}`

注册 API: `POST http://maf-openmoss:6565/api/agents/register`
Headers: `X-Registration-Token: {reg_token}`
Body: `{{"name": "{role_name}-agent", "role": "{role_name}", "description": "{role_name} agent for multi-agent-flow"}}`

注册完成后，你将获得 API Key 并开始工作。
"""

    async def configure_cron(self, agent_name: str, role_name: str) -> None:
        """
        为 Agent 配置 Cron 定时唤醒任务。
        BUG-02 修复：配置 delivery.channel 为 "last" 避免 Channel is required 错误
        """
        cron_id = f"{role_name}-poll"
        
        # 检查 Cron 是否已存在
        try:
            existing_crons = await openclaw_client.list_cron_jobs()
            if existing_crons and any(c.get('name') == cron_id for c in existing_crons):
                logger.info(f"Cron job {cron_id} already exists, skipping.")
                return
        except Exception as e:
            logger.warning(f"Failed to check existing cron jobs: {e}")
            # 继续执行，让 add_cron_job 处理重复情况
        
        # 获取角色的 Cron 配置，如果没有则使用默认
        cron_config = DEFAULT_CRON_CONFIGS.get(role_name, {})
        schedule = cron_config.get("schedule", "*/15 * * * *")
        message = cron_config.get("message", "Wake up and check tasks.")
        
        # BUG-02 修复：使用 CLI 配置 isolated session + best-effort-deliver 避免 Channel is required 错误
        cmd = [
            "docker", "exec", "maf-openclaw-gateway",
            "openclaw", "cron", "add",
            "--name", cron_id,
            "--agent", agent_name,
            "--cron", schedule,
            "--message", message,
            "--session", "isolated",
            "--channel", "last",
            "--best-effort-deliver"
        ]
        
        import asyncio
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            
            if proc.returncode == 0:
                logger.info(f"Cron job {cron_id} added successfully with isolated+best-effort delivery.")
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to add cron job {cron_id}: {error_msg}")
        except asyncio.TimeoutError:
            logger.error(f"Cron add timed out for {cron_id}")
        except Exception as e:
            logger.error(f"Exception adding cron job {cron_id}: {e}")

# 全局单例
agent_provisioner = AgentProvisioner()
