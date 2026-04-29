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

# P0 修复：所有 CLI 调用统一超时
CLI_TIMEOUT = 10.0


class OpenClawClient:
    """OpenClaw 客户端"""

    def __init__(self):
        self.base_url = settings.OPENCLAW_BASE_URL
        self.container_name = "maf-openclaw-gateway"
    
    def _validate_agent_name(self, name: str):
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', name):
            raise ValueError(f"Invalid agent name: {name}. Only alphanumeric and hyphens allowed.")
        if len(name) > 50:
            raise ValueError(f"Agent name too long: {len(name)} chars (max 50)")
    
    def _validate_model_name(self, model: str):
        import re
        if not re.match(r'^[a-zA-Z0-9./_-]+$', model):
            raise ValueError(f"Invalid model name: {model}")
        if len(model) > 100:
            raise ValueError(f"Model name too long: {len(model)} chars (max 100)")
    
    def _validate_workspace_path(self, path: str):
        import re
        if not re.match(r'^/[a-zA-Z0-9/_-]+$', path):
            raise ValueError(f"Invalid workspace path: {path}. Must start with / and contain only alphanumeric, underscores, hyphens, and slashes.")
        if '..' in path:
            raise ValueError(f"Invalid workspace path: {path}. Parent directory traversal not allowed.")

    async def _exec_cli(self, cmd: list, timeout: float = CLI_TIMEOUT) -> Dict[str, Any]:
        """
        P0 修复：统一 CLI 执行方法，带超时保护
        """
        logger.info(f"CLI: {' '.join(cmd[:5])}...")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            
            if proc.returncode == 0:
                return {"status": "success", "output": stdout.decode().strip()}
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"CLI failed: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            logger.error(f"CLI timed out after {timeout}s: {' '.join(cmd[:5])}")
            return {"status": "error", "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            logger.error(f"CLI exception: {e}")
            return {"status": "exception", "error": str(e)}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True
    )
    async def _request(self, method: str, url: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        headers = token_manager.get_headers(role="gateway", token_type="gateway")
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=headers, params=params, json=json, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/conversations/{conversation_id}"
        try:
            return await self._request("GET", url)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Conversation {conversation_id} not found")
                return {}
            raise

    async def list_conversations(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/conversations"
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", url, params=params)

    async def list_agents(self) -> List[str]:
        cmd = ["docker", "exec", self.container_name, "openclaw", "agents", "list"]
        result = await self._exec_cli(cmd)
        if result["status"] != "success":
            return []
        agent_ids = []
        for line in result["output"].split('\n'):
            line = line.strip()
            if line.startswith('- '):
                agent_id = line[2:].split()[0]
                agent_ids.append(agent_id)
        return agent_ids

    async def create_agent(self, name: str, model: str, workspace: str) -> Dict[str, Any]:
        self._validate_agent_name(name)
        self._validate_model_name(model)
        self._validate_workspace_path(workspace)
        workspace_arg = workspace if workspace else "/workspace"
        cmd = ["docker", "exec", self.container_name, "openclaw", "agents", "add", name, "--model", model, "--workspace", workspace_arg]
        return await self._exec_cli(cmd)

    async def send_message_to_agent(self, agent_name: str, content: str) -> Dict[str, Any]:
        cmd = ["docker", "exec", self.container_name, "openclaw", "agent", "--agent", agent_name, "-m", content]
        return await self._exec_cli(cmd)

    async def list_cron_jobs(self) -> List[Dict[str, Any]]:
        cmd = ["docker", "exec", self.container_name, "openclaw", "cron", "list", "--json"]
        result = await self._exec_cli(cmd)
        if result["status"] != "success":
            return []
        try:
            data = json.loads(result["output"])
            return data.get("jobs", [])
        except json.JSONDecodeError:
            return []

    async def add_cron_job(self, cron_id: str, agent_name: str, schedule: str, message: str) -> Dict[str, Any]:
        cmd = ["docker", "exec", self.container_name, "openclaw", "cron", "add", "--name", cron_id, "--agent", agent_name, "--cron", schedule, "--message", message]
        return await self._exec_cli(cmd)


# 全局单例
openclaw_client = OpenClawClient()
