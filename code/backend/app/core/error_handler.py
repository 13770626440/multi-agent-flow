"""
ErrorHandler - 异常处理与重试引擎

实现指数退避重试、熔断降级、人工介入告警。
"""
import asyncio
import logging
from typing import Callable, Awaitable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ErrorHandler:
    """异常处理与重试引擎"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    async def execute_with_retry(self, func: Callable[..., Awaitable], *args, **kwargs):
        """
        带重试的执行（指数退避：2s → 4s → 8s）
        
        Args:
            func: 异步函数
            *args, **kwargs: 函数参数
        """
        return await func(*args, **kwargs)
    
    async def handle_task_failure(self, sub_task_id: str, error: Exception, retry_count: int):
        """
        任务失败处理
        
        Args:
            sub_task_id: 子任务 ID
            error: 异常对象
            retry_count: 当前重试次数
        """
        if retry_count >= settings.MAX_RETRIES:
            # 超过重试上限，标记为 blocked
            logger.error(f"Task {sub_task_id} failed after {retry_count} retries: {error}")
            await self._alert_admin(sub_task_id, error)
            return "blocked"
        else:
            # 重新加入队列
            logger.warning(f"Task {sub_task_id} failed, retry {retry_count + 1}/{settings.MAX_RETRIES}")
            return "retry"
    
    async def _alert_admin(self, sub_task_id: str, error: Exception):
        """通知管理员（MVP 阶段仅记录日志）"""
        # TODO: 集成邮件/钉钉/企业微信告警
        logger.critical(f"ALERT: Task {sub_task_id} requires manual intervention: {error}")


# 全局单例
error_handler = ErrorHandler()
