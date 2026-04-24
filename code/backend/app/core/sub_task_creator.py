"""
SubTaskCreator - 子任务创建器

负责将 Decomposer 分解出的子任务列表批量创建到 OpenMOSS。
"""
import logging
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from app.clients.openmoss_client import openmoss_client

logger = logging.getLogger(__name__)


class SubTaskCreator:
    """子任务创建器"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True
    )
    async def create_sub_tasks(
        self,
        parent_task_id: str,
        sub_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量创建子任务到 OpenMOSS
        
        Args:
            parent_task_id: 父任务 ID
            sub_tasks: 子任务列表（来自 Decomposer）
        
        Returns:
            创建结果列表，包含 local_id、openmoss_id、name、dependencies
        
        Raises:
            Exception: OpenMOSS API 调用失败
        """
        created_tasks = []
        
        for i, sub_task in enumerate(sub_tasks):
            try:
                # 1. 构建 description（拼接 Skills + Instruction）
                description = self._build_description(sub_task)
                
                # 2. 构建 acceptance
                acceptance = "\n".join(sub_task.get("acceptance_criteria", []))
                
                # 3. 调用 OpenMOSS API
                response = await openmoss_client.create_sub_task(
                    task_id=parent_task_id,
                    name=sub_task["name"],
                    assigned_agent=sub_task.get("role", "executor"),
                    description=description,
                    acceptance=acceptance,
                    priority="medium",
                    type="once"
                )
                
                openmoss_id = response.get("id") or response.get("sub_task_id")
                
                created_tasks.append({
                    "local_id": sub_task.get("id", f"local_{i}"),
                    "openmoss_id": openmoss_id,
                    "name": sub_task["name"],
                    "role": sub_task.get("role", "executor"),
                    "dependencies": sub_task.get("dependencies", []),
                    "instruction": sub_task.get("instruction", ""),
                    "acceptance_criteria": sub_task.get("acceptance_criteria", [])
                })
                
                logger.info(f"Created sub-task in OpenMOSS: {sub_task['name']} -> {openmoss_id}")
                
            except Exception as e:
                logger.error(f"Failed to create sub-task '{sub_task.get('name')}': {e}")
                raise
        
        logger.info(f"Successfully created {len(created_tasks)} sub-tasks in OpenMOSS")
        return created_tasks
    
    def _build_description(self, sub_task: Dict) -> str:
        """
        构建 description（包含 Skills + Instruction + Output Format）
        
        Args:
            sub_task: 子任务定义
        
        Returns:
            格式化的 description（Markdown 格式）
        """
        parts = []
        
        # 1. Required Skills
        required_skills = sub_task.get("required_skills", [])
        if required_skills:
            skills_text = "\n".join([f"- {skill}" for skill in required_skills])
            parts.append(f"## Required Skills\n{skills_text}\n")
        
        # 2. Instruction
        instruction = sub_task.get("instruction", "")
        if instruction:
            parts.append(f"## Instruction\n{instruction}\n")
        
        # 3. Output Format
        output_format = sub_task.get("output_format")
        if output_format:
            parts.append(f"## Output Format\n{output_format}\n")
        
        # 4. Acceptance Criteria
        acceptance_criteria = sub_task.get("acceptance_criteria", [])
        if acceptance_criteria:
            criteria_text = "\n".join([f"- {c}" for c in acceptance_criteria])
            parts.append(f"## Acceptance Criteria\n{criteria_text}\n")
        
        return "\n".join(parts)
