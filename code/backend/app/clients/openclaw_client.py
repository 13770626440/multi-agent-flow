"""
OpenClawClient - OpenClaw 客户端

职责：
1. 获取 Agent 执行日志和会话历史（用于 Dashboard 展示和 QA 审计）。
2. 管理 Agent 生命周期（创建、配置）。
3. 发送消息给 Agent。
"""
import asyncio
import httpx
import json
import logging
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from app.core.token_manager import token_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenClawClient:
    """OpenClaw 客户端"""

    def __init__(self):
        self.base_url = settings.OPENCLAW_BASE_URL
        # OpenClaw 容器名称，用于 Docker Exec
        self.container_name = "maf-openclaw-gateway"
    
    def _validate_agent_name(self, name: str):
        """ARCH-002 修复：验证 Agent 名称"""
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', name):
            raise ValueError(f"Invalid agent name: {name}. Only alphanumeric and hyphens allowed.")
        if len(name) > 50:
            raise ValueError(f"Agent name too long: {len(name)} chars (max 50)")
    
    def _validate_model_name(self, model: str):
        """ARCH-002 修复：验证模型名称"""
        import re
        if not re.match(r'^[a-zA-Z0-9./_-]+$', model):
            raise ValueError(f"Invalid model name: {model}")
        if len(model) > 100:
            raise ValueError(f"Model name too long: {len(model)} chars (max 100)")
    
    def _validate_workspace_path(self, path: str):
        """ARCH-002 修复：验证工作区路径"""
        import re
        if not re.match(r'^/[a-zA-Z0-9/_-]+$', path):
            raise ValueError(f"Invalid workspace path: {path}. Must start with / and contain only alphanumeric, underscores, hyphens, and slashes.")
        if '..' in path:
            raise ValueError(f"Invalid workspace path: {path}. Parent directory traversal not allowed.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True
    )
    async def _request(self, method: str, url: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """
        内部通用请求方法，包含鉴权和重试逻辑
        """
        headers = token_manager.get_headers(role="gateway", token_type="gateway")
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=headers, params=params, json=json, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取指定会话的完整对话历史（用于审计/日志）
        对应 API: GET /api/v1/conversations/{id}
        """
        url = f"{self.base_url}/api/v1/conversations/{conversation_id}"
        try:
            return await self._request("GET", url)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Conversation {conversation_id} not found")
                return {}
            raise

    async def list_conversations(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取会话列表
        对应 API: GET /api/v1/conversations
        """
        url = f"{self.base_url}/api/v1/conversations"
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", url, params=params)

    async def list_agents(self) -> List[str]:
        """
        列出 OpenClaw 中已配置的 Agent ID 列表
        对应 CLI: openclaw agents list
        """
        cmd = [
            "docker", "exec", self.container_name,
            "openclaw", "agents", "list"
        ]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                output = stdout.decode().strip()
                # 解析输出，提取 agent ID（格式：- agent_id）
                agent_ids = []
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        agent_id = line[2:].split()[0]  # 取第一个词（ID）
                        agent_ids.append(agent_id)
                return agent_ids
            else:
                logger.error(f"Failed to list agents: {stderr.decode().strip()}")
                return []
                
        except Exception as e:
            logger.error(f"Exception while listing agents: {e}")
            return []

    async def create_agent(self, name: str, model: str, workspace: str) -> Dict[str, Any]:
        """
        通过 Docker Exec CLI 创建 Agent (方案 B)
        对应 CLI: docker exec maf-openclaw-gateway openclaw agents add {name} --model {model} --workspace {workspace}
        
        注意：此方法要求 Backend 容器具有执行 docker 命令的权限（通常需挂载 /var/run/docker.sock）。
        """
        # ARCH-002 修复：输入验证
        self._validate_agent_name(name)
        self._validate_model_name(model)
        self._validate_workspace_path(workspace)
        
        # 使用 workspace 参数或默认值
        workspace_arg = workspace if workspace else "/workspace"
        
        cmd = [
            "docker", "exec", self.container_name, 
            "openclaw", "agents", "add", name, 
            "--model", model,
            "--workspace", workspace_arg
        ]
        
        logger.info(f"Executing CLI to create agent: {' '.join(cmd)}")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                logger.info(f"Agent {name} created successfully via CLI.")
                return {"status": "success", "name": name, "output": stdout.decode().strip()}
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to create agent {name}: {error_msg}")
                return {"status": "error", "name": name, "error": error_msg}
                
        except Exception as e:
            logger.error(f"Exception while creating agent {name}: {e}")
            return {"status": "exception", "name": name, "error": str(e)}

    async def send_message_to_agent(self, agent_name: str, content: str) -> Dict[str, Any]:
        """
        发送消息给指定 Agent（使用 CLI 命令）
        对应 CLI: openclaw agent --agent {agent_name} -m "{content}"
        """
        # 使用 CLI 命令发送消息
        cmd = [
            "docker", "exec", self.container_name,
            "openclaw", "agent",
            "--agent", agent_name,
            "-m", content
        ]
        
        logger.info(f"Sending message to agent via CLI: {agent_name}")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                logger.info(f"Message sent to {agent_name} successfully.")
                return {"status": "success", "output": stdout.decode().strip()}
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to send message to {agent_name}: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Exception while sending message to {agent_name}: {e}")
            return {"status": "exception", "error": str(e)}

    async def list_cron_jobs(self) -> List[Dict[str, Any]]:
        """
        列出所有 Cron 任务
        对应 CLI: openclaw cron list --json
        """
        cmd = [
            "docker", "exec", self.container_name,
            "openclaw", "cron", "list", "--json"
        ]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                output = stdout.decode().strip()
                data = json.loads(output)
                return data.get("jobs", [])
            else:
                logger.error(f"Failed to list cron jobs: {stderr.decode().strip()}")
                return []
                
        except Exception as e:
            logger.error(f"Exception while listing cron jobs: {e}")
            return []

    async def add_cron_job(self, cron_id: str, agent_name: str, schedule: str, message: str) -> Dict[str, Any]:
        """
        添加 Cron 定时任务（使用 CLI 命令）
        对应 CLI: openclaw cron add --name {cron_id} --agent {agent_name} --cron {schedule} --message {message}
        """
        cmd = [
            "docker", "exec", self.container_name,
            "openclaw", "cron", "add",
            "--name", cron_id,
            "--agent", agent_name,
            "--cron", schedule,
            "--message", message
        ]
        
        logger.info(f"Adding cron job {cron_id} for agent {agent_name} via CLI")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                logger.info(f"Cron job {cron_id} added successfully.")
                return {"status": "success", "output": stdout.decode().strip()}
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to add cron job {cron_id}: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Exception while adding cron job {cron_id}: {e}")
            return {"status": "exception", "error": str(e)}


# 全局单例
openclaw_client = OpenClawClient()
