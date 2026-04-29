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
from app.clients.openmoss_auth import OpenMOSSAuth

logger = logging.getLogger(__name__)

settings = get_settings()


class OpenMOSSClient:
    """OpenMOSS API 客户端"""
    
    def __init__(self):
        self.base_url = settings.OPENMOSS_BASE_URL
        self.timeout = 10.0
    
    def _get_headers(self, role: str) -> Dict[str, str]:
        """获取请求头（委托给 OpenMOSSAuth 工具类）"""
        return OpenMOSSAuth.get_headers(role)

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
        
        Raises:
            httpx.HTTPStatusError: 401/403 认证错误，不重试
            httpx.ConnectError / httpx.TimeoutException: 网络错误，触发重试
        """
        headers = self._get_headers(role)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
            # 401/403 认证错误不应重试
            if response.status_code in (401, 403):
                logger.error(f"OpenMOSS auth failed ({response.status_code})")
                response.raise_for_status()
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
    # OpenMOSS 子任务状态机：
    # pending → assigned（创建时设置 assigned_agent 或 planner reassign）
    # assigned/rework → in_progress（executor start）
    # in_progress → review（executor submit）
    # review → done（reviewer complete）
    # review → rework（reviewer rework，返工后回 in_progress）
    # 任意非终态 → blocked（patrol block）

    async def start_sub_task(self, sub_task_id: str, session_id: str) -> Dict[str, Any]:
        """开始执行子任务 (Executor 调用): assigned/rework → in_progress
        
        前置条件：子任务状态必须为 assigned 或 rework
        """
        return await self.update_sub_task_status(sub_task_id, "start", "executor", session_id)

    async def submit_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """提交子任务成果 (Executor 调用): in_progress → review
        
        前置条件：子任务状态必须为 in_progress（需先调用 start_sub_task）
        注意：submit API 不需要 session_id 参数
        """
        return await self.update_sub_task_status(sub_task_id, "submit", "executor")
    
    async def complete_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """审查通过子任务 (Reviewer 调用): review → done"""
        return await self.update_sub_task_status(sub_task_id, "complete", "reviewer")
    
    async def rework_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """驳回子任务返工 (Reviewer 调用): review → rework"""
        return await self.update_sub_task_status(sub_task_id, "rework", "reviewer")

    async def block_sub_task(self, sub_task_id: str) -> Dict[str, Any]:
        """标记子任务为阻塞 (Patrol 调用)"""
        return await self.update_sub_task_status(sub_task_id, "block", "patrol")

    # --- Agent 管理方法 ---

    async def list_agents(self) -> List[Dict[str, Any]]:
        """
        获取已注册的 Agent 列表
        对应 API: GET /api/agents
        """
        url = f"{self.base_url}/api/agents"
        try:
            result = await self._request("GET", url, "planner")
            
            # 兼容不同的返回格式
            if isinstance(result, list):
                return result
            return result.get("items", result.get("agents", []))
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                logger.error(f"OpenMOSS auth failed: {e.response.status_code}")
                raise
            logger.warning(f"Failed to list agents: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing agents: {e}")
            return []

    async def get_prompt(self, role: str) -> str:
        """
        获取指定角色的提示词
        对应 API: GET /api/admin/prompts/onboarding/{role}
        
        注意：此接口需要管理员认证，暂时返回空字符串
        TODO: 配置管理员 token 或提供默认 prompt
        """
        # 暂时返回默认 prompt，因为 /api/admin/prompts/onboarding/{role} 需要管理员认证
        logger.warning(f"Prompt API requires admin auth, returning default prompt for role: {role}")
        return f"""你是 {role} 角色。请按照任务指令执行任务。

## 职责
- 接收并理解任务指令
- 按照要求执行任务
- 提交执行结果

## 工作规范
1. 收到任务后，仔细阅读指令
2. 按要求完成任务
3. 将结果输出到指定格式
"""

    async def get_tool_cli(self) -> str:
        """
        获取 task-cli.py 内容
        对应 API: GET /api/tools/cli
        """
        url = f"{self.base_url}/api/tools/cli"
        try:
            result = await self._request("GET", url, "planner")
            return result.get("content", "")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get CLI tool: {e.response.status_code}")
            return ""
        except httpx.ConnectError as e:
            logger.error(f"Connection failed getting CLI tool: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error getting CLI tool: {e}")
            return ""

    async def get_skill_md(self, role: str) -> str:
        """
        获取 Skill 文档 (Agent 自动注册后下载)
        对应 API: GET /api/agents/me/skill
        
        Args:
            role: Agent 角色
        
        Returns:
            Skill 文档内容
        """
        url = f"{self.base_url}/api/agents/me/skill"
        try:
            headers = OpenMOSSAuth.get_headers(role)
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=self.timeout)
                if response.status_code == 404:
                    logger.warning(f"Skill not found for role: {role}")
                    return ""
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get skill for role {role}: {e.response.status_code}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error getting skill for role {role}: {e}")
            return ""


# 全局单例
openmoss_client = OpenMOSSClient()
