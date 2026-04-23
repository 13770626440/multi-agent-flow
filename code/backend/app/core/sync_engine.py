"""
SyncEngine - 状态同步引擎

负责定期轮询 OpenMOSS 状态，同步到 Backend 数据库，并触发后续任务。
"""
import asyncio
import logging
from typing import List, Dict, Any

from app.config import get_settings
from app.core.database import async_session
from app.models.task import SubTaskRecord, SubTaskStatus, TaskInstance, TaskStatus
from app.core.dag_engine import DAGEngine
from app.core.dispatcher import dispatcher

logger = logging.getLogger(__name__)

settings = get_settings()


class SyncEngine:
    """状态同步引擎"""
    
    def __init__(self):
        self.sync_interval = settings.SYNC_INTERVAL_SECONDS  # 默认 300 秒（5 分钟）
    
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
                SubTaskRecord.__table__.select().where(
                    SubTaskRecord.status.in_([
                        SubTaskStatus.ASSIGNED,
                        SubTaskStatus.IN_PROGRESS,
                        SubTaskStatus.REVIEW
                    ])
                )
            )
            sub_tasks = result.fetchall()
            
            for row in sub_tasks:
                sub_task = SubTaskRecord(**row._mapping)
                await self.sync_sub_task(session, sub_task)
            
            await session.commit()
    
    async def sync_sub_task(self, session, sub_task: SubTaskRecord):
        """同步单个子任务状态"""
        if not sub_task.openmoss_id:
            return  # 尚未创建 OpenMOSS 子任务
        
        # TODO: 调用 OpenMOSS API 获取最新状态
        # om_status = await openmoss_client.get_sub_task(sub_task.openmoss_id)
        
        # 模拟状态映射
        # status_map = {
        #     "done": SubTaskStatus.DONE,
        #     "review": SubTaskStatus.REVIEW,
        #     "in_progress": SubTaskStatus.IN_PROGRESS,
        #     "rework": SubTaskStatus.REWORK,
        #     "blocked": SubTaskStatus.BLOCKED
        # }
        # new_status = status_map.get(om_status["status"])
        # if new_status and new_status != sub_task.status:
        #     sub_task.status = new_status
        #     if new_status == SubTaskStatus.DONE:
        #         await self._unlock_dependent_tasks(session, sub_task)
        pass
    
    async def _unlock_dependent_tasks(self, session, completed_task: SubTaskRecord):
        """解锁依赖当前任务的后续任务"""
        # 1. 获取父任务 DAG 快照
        # 2. 找出依赖当前任务的后续任务
        # 3. 更新状态为 ASSIGNED
        # 4. 调用 Dispatcher 派发
        pass


# 全局单例
sync_engine = SyncEngine()
