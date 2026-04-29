"""
SyncEngine - 状态同步引擎

负责定期轮询 OpenMOSS 状态，同步到 Backend 数据库，并触发后续任务。
"""
import asyncio
import logging
from typing import List, Dict, Any
from sqlalchemy import select

from app.config import get_settings
from app.core.database import async_session
from app.models.task import SubTaskRecord, SubTaskStatus, TaskInstance, TaskStatus
from app.core.dag_engine import DAGEngine
from app.core.dispatcher import dispatcher
from app.core.decomposer import Decomposer
from app.clients.openmoss_client import openmoss_client

logger = logging.getLogger(__name__)

settings = get_settings()

# OpenMOSS 状态到本地状态的映射
OPENMOSS_STATUS_MAP = {
    "done": SubTaskStatus.DONE,
    "completed": SubTaskStatus.DONE,
    "review": SubTaskStatus.REVIEW,
    "in_progress": SubTaskStatus.IN_PROGRESS,
    "running": SubTaskStatus.IN_PROGRESS,
    "rework": SubTaskStatus.REWORK,
    "rejected": SubTaskStatus.REWORK,
    "blocked": SubTaskStatus.BLOCKED,
    "assigned": SubTaskStatus.ASSIGNED,
    "pending": SubTaskStatus.PENDING,
}


class SyncEngine:
    """状态同步引擎"""
    
    def __init__(self):
        self.sync_interval = settings.SYNC_INTERVAL_SECONDS  # 默认 300 秒（5 分钟）
        self.decomposer = Decomposer()  # 用于处理动态任务分解完成通知
    
    async def start_sync_loop(self):
        """启动同步循环（后台任务）"""
        logger.info(f"SyncEngine started, interval: {self.sync_interval}s")
        while True:
            try:
                await self.sync_all_tasks()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
            await asyncio.sleep(self.sync_interval)
    
    async def sync_all_tasks(self):
        """同步所有进行中的任务"""
        async with async_session() as session:
            # 获取所有进行中的子任务
            result = await session.execute(
                select(SubTaskRecord).where(
                    SubTaskRecord.status.in_([
                        SubTaskStatus.ASSIGNED,
                        SubTaskStatus.IN_PROGRESS,
                        SubTaskStatus.REVIEW
                    ])
                )
            )
            sub_tasks = result.scalars().all()
            
            logger.info(f"Syncing {len(sub_tasks)} active sub-tasks")
            
            for sub_task in sub_tasks:
                await self.sync_sub_task(session, sub_task)
            
            await session.commit()
    
    async def sync_sub_task(self, session, sub_task: SubTaskRecord):
        """同步单个子任务状态"""
        if not sub_task.openmoss_id:
            logger.warning(f"Sub-task {sub_task.id} has no openmoss_id, skipping")
            return  # 尚未创建 OpenMOSS 子任务
        
        try:
            # 调用 OpenMOSS API 获取最新状态
            om_status = await openmoss_client.get_sub_task(sub_task.openmoss_id)
            
            # 状态映射
            om_status_str = om_status.get("status", "").lower()
            new_status = OPENMOSS_STATUS_MAP.get(om_status_str)
            
            if new_status and new_status != sub_task.status:
                old_status = sub_task.status
                sub_task.status = new_status
                logger.info(
                    f"Sub-task {sub_task.id} status changed: "
                    f"{old_status.value} -> {new_status.value} "
                    f"(OpenMOSS: {om_status_str})"
                )
                
                # 如果任务完成，处理完成逻辑
                if new_status == SubTaskStatus.DONE:
                    # 检查是否为动态分解任务
                    if getattr(sub_task, 'is_decomposition_task', False):
                        await self._handle_decomposition_complete(session, sub_task, om_status)
                    else:
                        # 普通任务，解锁后续依赖
                        await self._unlock_dependent_tasks(session, sub_task)
                
                # 如果任务被驳回，记录日志
                elif new_status == SubTaskStatus.REWORK:
                    logger.warning(f"Sub-task {sub_task.id} requires rework")
                
                # 如果任务被阻塞，记录日志
                elif new_status == SubTaskStatus.BLOCKED:
                    logger.warning(f"Sub-task {sub_task.id} is blocked")
        
        except Exception as e:
            logger.error(f"Failed to sync sub-task {sub_task.id}: {e}")
            # 不抛出异常，继续处理下一个任务
    
    async def _unlock_dependent_tasks(self, session, completed_task: SubTaskRecord):
        """解锁依赖当前任务的后续任务（ARCH-003 修复：统一使用 task_id）"""
        # 1. 获取父任务 DAG 快照
        result = await session.execute(
            select(TaskInstance).where(TaskInstance.id == completed_task.instance_id)
        )
        task_instance = result.scalar_one_or_none()
        
        if not task_instance:
            logger.error(f"Task instance {completed_task.instance_id} not found")
            return
        
        dag_snapshot = task_instance.dag_snapshot
        if not dag_snapshot:
            logger.warning(f"No DAG snapshot for task {completed_task.instance_id}")
            return
        
        # ARCH-003 修复：构建 task_id 到 SubTaskRecord 的映射
        all_sub_tasks_result = await session.execute(
            select(SubTaskRecord).where(SubTaskRecord.instance_id == completed_task.instance_id)
        )
        all_sub_tasks = all_sub_tasks_result.scalars().all()
        
        # 建立 task_id (UUID) -> SubTaskRecord 映射
        # 注意：SubTaskRecord.id 是 UUID，但 dependencies 存储的也是 UUID
        # 所以这里直接使用 UUID 比较即可
        task_id_to_record = {task.id: task for task in all_sub_tasks}
        
        # 2. 找出依赖当前完成任务的后续任务
        unlocked_count = 0
        
        for task_record in all_sub_tasks:
            # 跳过已完成或当前任务
            if task_record.status in [SubTaskStatus.DONE, SubTaskStatus.FAILED]:
                continue
            if task_record.id == completed_task.id:
                continue
            
            # 检查是否依赖当前完成的任务
            dependencies = task_record.dependencies or []
            if completed_task.id not in dependencies:
                continue
            
            # 检查所有依赖是否都已完成
            all_deps_done = await self._check_all_dependencies_done(
                session, completed_task.instance_id, task_record
            )
            
            if all_deps_done and task_record.status == SubTaskStatus.PENDING:
                # 解锁任务
                task_record.status = SubTaskStatus.ASSIGNED
                unlocked_count += 1
                logger.info(f"Unlocked dependent task {task_record.id}")
                
                # 调用 Dispatcher 派发任务
                try:
                    dispatch_result = await dispatcher.dispatch_task(
                        sub_task_id=task_record.id,
                        openmoss_id=task_record.openmoss_id or "",
                        role=task_record.role,
                        instruction=task_record.instruction,
                        conversation_id=task_record.conversation_id
                    )
                    task_record.dispatch_status = dispatch_result["status"]
                    logger.info(f"Dispatched unlocked task {task_record.id}: {dispatch_result['status']}")
                except Exception as e:
                    logger.error(f"Failed to dispatch unlocked task {task_record.id}: {e}")
                    task_record.dispatch_status = "failed"
        
        if unlocked_count > 0:
            logger.info(f"Unlocked {unlocked_count} dependent tasks for {completed_task.instance_id}")
    
    async def _check_all_dependencies_done(self, session, instance_id, sub_task) -> bool:
        """检查子任务的所有依赖是否都已完成"""
        if not sub_task.dependencies:
            return True  # 没有依赖
        
        # 查询所有依赖的子任务
        dep_ids = sub_task.dependencies
        result = await session.execute(
            select(SubTaskRecord).where(
                SubTaskRecord.instance_id == instance_id,
                SubTaskRecord.id.in_(dep_ids)
            )
        )
        dep_tasks = result.scalars().all()
        
        # 检查是否所有依赖都已完成
        for dep_task in dep_tasks:
            if dep_task.status != SubTaskStatus.DONE:
                return False
        
        return True
    
    async def _handle_decomposition_complete(
        self, 
        session, 
        sub_task: SubTaskRecord, 
        om_status: Dict
    ):
        """
        处理动态分解任务完成
        
        Args:
            session: 数据库会话
            sub_task: 子任务记录
            om_status: OpenMOSS 返回的状态信息
        """
        logger.info(f"Handling decomposition completion for {sub_task.id}")
        
        try:
            # 1. 从 OpenMOSS 状态信息中获取输出
            # 尝试多个可能的字段名称
            output = (
                om_status.get("output", "") or 
                om_status.get("deliverable", "") or 
                om_status.get("result", "") or
                om_status.get("description", "")
            )
            
            # 2. 保存到数据库
            sub_task.decomposition_output = output
            
            # 3. 通知 Decomposer 任务完成
            self.decomposer.notify_completion(
                sub_task.openmoss_id,
                {"output": output}
            )
            
            logger.info(
                f"Notified decomposition completion for {sub_task.openmoss_id}, "
                f"output length: {len(output) if output else 0}"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle decomposition complete for {sub_task.id}: {e}")
            # 通知失败，标记任务为失败
            self.decomposer.notify_failure(
                sub_task.openmoss_id,
                f"Failed to handle decomposition: {str(e)}"
            )


# 全局单例
sync_engine = SyncEngine()
