"""
ReviewEngine - 评审引擎

负责处理任务评审流程，包括：
1. 创建评审任务
2. 处理评审通过（解锁后续任务）
3. 处理评审驳回（创建修正任务）
"""
import logging
from typing import Dict, Any, List

from app.clients.openmoss_client import openmoss_client
from app.core.dispatcher import dispatcher

logger = logging.getLogger(__name__)


class ReviewEngine:
    """评审引擎"""
    
    async def handle_task_review(self, sub_task: Dict[str, Any]):
        """
        处理任务评审
        
        Args:
            sub_task: 子任务信息（来自 OpenMOSS）
        """
        # 1. 获取验收标准
        acceptance_criteria = self._parse_acceptance_criteria(sub_task.get("acceptance", ""))
        
        # 2. 创建评审任务
        review_task = await self._create_review_task(sub_task, acceptance_criteria)
        
        logger.info(f"Review task created for {sub_task.get('id', 'unknown')}")
        return review_task
    
    async def _create_review_task(
        self,
        sub_task: Dict[str, Any],
        acceptance_criteria: List[str]
    ) -> Dict[str, Any]:
        """创建评审任务"""
        description = f"""## Review Task

请评审以下子任务的产出物：

**子任务名称**: {sub_task.get('name', 'unknown')}
**子任务 ID**: {sub_task.get('id', 'unknown')}

## Acceptance Criteria
{chr(10).join([f"- {c}" for c in acceptance_criteria])}

请逐项检查并给出评审结果（通过/驳回）。
"""
        
        response = await openmoss_client.create_sub_task(
            task_id=sub_task.get('task_id', ''),
            name=f"评审：{sub_task.get('name', 'unknown')}",
            assigned_agent="reviewer",
            description=description,
            acceptance="\n".join(acceptance_criteria),
            priority="high"
        )
        
        return response
    
    async def handle_review_passed(self, sub_task: Dict[str, Any]):
        """
        处理评审通过
        
        Args:
            sub_task: 子任务信息
        """
        logger.info(f"Review passed for {sub_task.get('id', 'unknown')}")
        # 解锁后续依赖任务（由 SyncEngine 处理）
    
    async def handle_review_failed(
        self,
        sub_task: Dict[str, Any],
        comments: str
    ):
        """
        处理评审驳回
        
        Args:
            sub_task: 子任务信息
            comments: 评审意见
        """
        logger.warning(f"Review failed for {sub_task.get('id', 'unknown')}: {comments}")
        
        # 创建修正任务
        rework_task = await self._create_rework_task(sub_task, comments)
        
        # 派发修正任务
        await dispatcher.dispatch_task(
            sub_task_id=rework_task['id'],
            openmoss_id=rework_task['openmoss_id'],
            role=sub_task.get('role', 'executor'),
            instruction=rework_task['instruction'],
            conversation_id=f"rework_{sub_task.get('id', 'unknown')}"
        )
        
        return rework_task
    
    async def _create_rework_task(
        self,
        sub_task: Dict[str, Any],
        comments: str
    ) -> Dict[str, Any]:
        """创建修正任务"""
        instruction = f"""
你的任务未通过评审，请根据以下意见修正：

## 评审意见
{comments}

## 原始任务
{sub_task.get('instruction', '')}

请修正后重新提交。
"""
        
        response = await openmoss_client.create_sub_task(
            task_id=sub_task.get('task_id', ''),
            name=f"修正：{sub_task.get('name', 'unknown')}",
            assigned_agent=sub_task.get('assigned_agent', 'executor'),
            description=instruction,
            acceptance=sub_task.get('acceptance', ''),
            priority="high"
        )
        
        return {
            "id": f"{sub_task.get('id', 'unknown')}-rework",
            "openmoss_id": response.get("id"),
            "instruction": instruction
        }
    
    def _parse_acceptance_criteria(self, acceptance: str) -> List[str]:
        """
        解析验收标准（从多行文本）
        
        Args:
            acceptance: 验收标准文本
        
        Returns:
            验收标准列表
        """
        if not acceptance:
            return []
        
        criteria = []
        for line in acceptance.split('\n'):
            line = line.strip('- ').strip()
            if line:
                criteria.append(line)
        
        return criteria
