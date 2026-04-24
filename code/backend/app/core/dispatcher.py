"""
Dispatcher - 任务派发服务

实现"推拉结合"的派发机制：
- 主推 (Push): 通过 OpenClaw API 实时注入指令
- 备拉 (Pull): 在 OpenMOSS 中标记任务，等待 Agent 轮询拉取
"""
import httpx
import uuid
import logging
from typing import Optional

from app.config import get_settings
from app.core.token_manager import token_manager

logger = logging.getLogger(__name__)

settings = get_settings()


class Dispatcher:
    """任务派发服务"""
    
    def __init__(self):
        self.openclaw_base_url = settings.OPENCLAW_BASE_URL
        self.openmoss_base_url = settings.OPENMOSS_BASE_URL
    
    async def dispatch_task(
        self,
        sub_task_id: str,
        openmoss_id: str,
        role: str,
        instruction: str,
        conversation_id: Optional[str] = None
    ) -> dict:
        """
        派发任务：主推 + 备拉双保险
        
        Args:
            sub_task_id: 子任务 ID
            openmoss_id: OpenMOSS 子任务 ID
            role: 执行角色
            instruction: 任务指令
            conversation_id: OpenClaw 会话 ID（可选，自动生成）
            
        Returns:
            {"status": "pushed" | "pending_pull", "conversation_id": str}
        """
        if not conversation_id:
            conversation_id = f"task_{sub_task_id}"
        
        try:
            # 1. 主推模式：实时调用 OpenClaw API
            await self._push_to_openclaw(conversation_id, instruction)
            logger.info(f"Task {sub_task_id} dispatched via Push to {role}")
            return {"status": "pushed", "conversation_id": conversation_id}
            
        except Exception as e:
            logger.warning(f"OpenClaw Push failed for task {sub_task_id}: {e}, falling back to Pull")
            # 2. 备拉模式：仅更新 OpenMOSS 状态，等待 Agent 轮询
            await self._pull_fallback(openmoss_id, role)
            logger.info(f"Task {sub_task_id} dispatched via Pull fallback to {role}")
            return {"status": "pending_pull", "conversation_id": conversation_id}
    
    async def _push_to_openclaw(self, conversation_id: str, instruction: str):
        """主推：调用 OpenClaw 消息注入 API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.openclaw_base_url}/api/v1/message",
                headers=token_manager.get_headers("gateway", "gateway"),
                json={
                    "channel": "api",
                    "message": instruction,
                    "conversation_id": conversation_id,
                    "wait_for_response": False  # 异步模式，不阻塞
                },
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    
    async def _pull_fallback(self, openmoss_id: str, role: str):
        """备拉：在 OpenMOSS 中标记任务为 assigned，等待 Agent 轮询
        
        注意：OpenMOSS 创建子任务时已通过 assigned_agent 参数分配角色，
        Agent 的 Cron 脚本会定期轮询 GET /api/sub-tasks/mine 发现新任务。
        此处无需额外 API 调用，仅记录日志用于追踪。
        """
        logger.info(
            f"Pull fallback: task {openmoss_id} already assigned to {role} at creation time. "
            f"Agent will poll via Cron."
        )
        return {"status": "pending_pull"}
    
    async def dispatch_batch(self, sub_tasks: list) -> list:
        """
        批量派发任务
        
        Args:
            sub_tasks: 子任务列表，每个包含 id, openmoss_id, role, instruction
            
        Returns:
            派发结果列表
        """
        results = []
        for task in sub_tasks:
            result = await self.dispatch_task(
                sub_task_id=task["id"],
                openmoss_id=task["openmoss_id"],
                role=task["role"],
                instruction=task["instruction"],
                conversation_id=task.get("conversation_id")
            )
            results.append(result)
        return results


# 全局单例
dispatcher = Dispatcher()
