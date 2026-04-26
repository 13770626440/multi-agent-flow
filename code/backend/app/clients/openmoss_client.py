"""
OpenMOSSClient - OpenMOSS API 客户端封装

封装 OpenMOSS 的 Sub-Task 管理 API，供 Backend 调用。
包含重试机制、快捷方法和完善的日志记录。
"""
import httpx
import logging
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from app.core.token_manager import token_manager

logger = logging.getLogger(__name__)

settings = get_settings()


class OpenMOSSClient:
    """OpenMOSS API 客户端"""
    
    def __init__(self):
        self.base_url = settings.OPENMOSS_BASE_URL
        self.timeout = 10.0
    
    def _get_headers(self, role: str) -> Dict[str, str]:
        """获取请求头（OpenMOSS 使用 Authorization Bearer）"""
        token = token_manager.get_token(role)
        return {"Authorization": f"Bearer {token}"}

    async def create_task(
        self,
        name: str,
        description: str = "",
        task_type: str = "once"
    ) -> Dict[str, Any]:
        """
        创建任务 (Planner 调用)
        """
        url = f"{self.base_url}/api/tasks"
        payload = {
            "name": name,
            "description": description,
            "type": task_type
        }
        logger.info(f"Creating task in OpenMOSS: {name}")
        return await self._request("POST", url, "planner", json=payload)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True
    )
    async def _request(self, method: str, url: str, role: str, **kwargs) -> Dict[str, Any]:
        """
        通用请求方法，包含重试逻辑
        
        Args:
            method: HTTP 方法 (GET/POST)
            url: 请求 URL
            role: Agent 角色 (用于获取 Token)
            **kwargs: 其他请求参数 (json, params 等)
        """
        headers = self._get_headers(role)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
            response.raise_for_status()
            return response.json()

    async def create_sub_task(
        self,
        task_id: str,
        name: str,
        description: Optional[str] = None,
        deliverable: Optional[str] = None,
        acceptance: Optional[str] = None,
        priority: str = "medium",
        assigned_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建子任务 (Planner 调用)
        注意：assigned_agent 需要是 Agent ID，不是角色名称。
        如果不传递，子任务状态为 pending，等待 Agent 认领。
        """
        url = f"{self.base_url}/api/sub-tasks"
        payload = {
            "task_id": task_id,
            "name": name,
            "description": description or "",
            "deliverable": deliverable or "",
            "acceptance": acceptance or "",
            "priority": priority,
            "type": "once"
        }
        if assigned_agent:
            payload["assigned_agent"] = assigned_agent
        
        logger.info(f"Creating sub-task: {name} for task {task_id}")
        return await self._request("POST", url, "planner", json=payload)
    
    async def get_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """
        获取子任务详情 (Planner 调用)
        """
        url = f"{self.base_url}/api/sub-tasks/{sub_task_id}"
        return await self._request("GET", url, "planner")
    
    async def list_sub_tasks(
        self,
        task_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询子任务列表 (Planner 调用)
        """
        url = f"{self.base_url}/api/sub-tasks"
        params = {}
        if task_id: params["task_id"] = task_id
        if status: params["status"] = status
        
        result = await self._request("GET", url, "planner", params=params)
        return result.get("items", [])
    
    async def update_sub_task_status(
        self,
        sub_task_id: str,
        action: str,
        agent_role: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新子任务状态 (通用方法)
        """
        url = f"{self.base_url}/api/sub-tasks/{sub_task_id}/{action}"
        payload = {}
        if session_id: payload["session_id"] = session_id
        
        logger.info(f"Updating sub-task {sub_task_id} status: {action} by {agent_role}")
        return await self._request("POST", url, agent_role, json=payload)

    # --- 快捷方法 ---

    async def start_sub_task(self, sub_task_id: str, session_id: str) -> Dict[str, Any]:
        """开始执行子任务 (Executor 调用)"""
        return await self.update_sub_task_status(sub_task_id, "start", "executor", session_id)

    async def submit_sub_task(self, sub_task_id: str, session_id: str) -> Dict[str, Any]:
        """提交子任务成果 (Executor 调用)"""
        return await self.update_sub_task_status(sub_task_id, "submit", "executor", session_id)
    
    async def complete_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """审查通过子任务 (Reviewer 调用)"""
        return await self.update_sub_task_status(sub_task_id, "complete", "reviewer")
    
    async def rework_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """驳回子任务返工 (Reviewer 调用)"""
        return await self.update_sub_task_status(sub_task_id, "rework", "reviewer")

    async def block_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """标记子任务为阻塞 (Patrol 调用)"""
        return await self.update_sub_task_status(sub_task_id, "block", "patrol")


# 全局单例
openmoss_client = OpenMOSSClient()
