"""
OpenClawClient - OpenClaw 客户端

职责：
1. 获取 Agent 执行日志和会话历史（用于 Dashboard 展示和 QA 审计）。
2. 管理 Agent 生命周期（创建、配置）。
3. 发送消息给 Agent。
"""
import httpx
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

    async def create_agent(self, name: str, model: str, workspace: str) -> Dict[str, Any]:
        """
        创建新的 Agent
        对应 CLI: openclaw agents add {name} --model {model} --workspace {workspace}
        对应 API: POST /api/agents (假设路径)
        """
        url = f"{self.base_url}/api/agents"
        payload = {
            "name": name,
            "model": model,
            "workspace": workspace
        }
        logger.info(f"Creating OpenClaw agent: {name} with model {model}")
        return await self._request("POST", url, json=payload)

    async def send_message_to_agent(self, agent_name: str, content: str) -> Dict[str, Any]:
        """
        发送消息给指定 Agent
        对应 API: POST /api/agents/{name}/message
        """
        url = f"{self.base_url}/api/agents/{agent_name}/message"
        payload = {"content": content}
        logger.info(f"Sending message to agent: {agent_name}")
        return await self._request("POST", url, json=payload)

    async def add_cron_job(self, cron_id: str, agent_name: str, schedule: str, message: str) -> Dict[str, Any]:
        """
        添加 Cron 定时任务
        对应 CLI: openclaw cron add {id} --schedule {schedule} --agent {agent} --message {message}
        对应 API: POST /api/cron
        """
        url = f"{self.base_url}/api/cron"
        payload = {
            "id": cron_id,
            "agent": agent_name,
            "schedule": schedule,
            "message": message
        }
        logger.info(f"Adding cron job {cron_id} for agent {agent_name}")
        return await self._request("POST", url, json=payload)


# 全局单例
openclaw_client = OpenClawClient()
