"""
数据库模型定义

包含 TaskInstance 和 SubTaskRecord 模型。
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubTaskStatus(str, enum.Enum):
    """子任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    REWORK = "rework"
    BLOCKED = "blocked"


class DispatchStatus(str, enum.Enum):
    """派发状态枚举"""
    PUSHED = "pushed"              # 主推成功
    PENDING_PULL = "pending_pull"  # 降级为备拉
    FAILED = "failed"              # 派发失败


class TaskInstance(Base):
    """任务实例模型"""
    __tablename__ = "task_instances"
    
    id = Column(String(36), primary_key=True)
    template_id = Column(String(36), nullable=True, comment="关联的模板 ID")
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    dag_snapshot = Column(JSON, nullable=True, comment="DAG 完整快照")
    user_id = Column(String(36), nullable=True, comment="创建用户 ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联子任务
    sub_tasks = relationship("SubTaskRecord", back_populates="task_instance", cascade="all, delete-orphan")


class SubTaskRecord(Base):
    """子任务记录模型"""
    __tablename__ = "sub_task_records"
    
    id = Column(String(36), primary_key=True)
    instance_id = Column(String(36), ForeignKey("task_instances.id"), nullable=False, comment="所属任务实例 ID")
    openmoss_id = Column(String(36), nullable=True, comment="OpenMOSS 中的子任务 ID")
    name = Column(String(255), nullable=False, comment="子任务名称")
    role = Column(String(50), nullable=False, comment="执行角色")
    status = Column(Enum(SubTaskStatus), default=SubTaskStatus.PENDING, comment="子任务状态")
    conversation_id = Column(String(255), nullable=True, comment="OpenClaw 会话 ID")
    instruction = Column(Text, nullable=True, comment="任务指令")
    output = Column(Text, nullable=True, comment="执行结果")
    decomposition_basis = Column(Text, nullable=True, comment="分解依据（仅动态任务）")
    dependencies = Column(JSON, default=list, comment="依赖的子任务 ID 列表")
    retry_count = Column(Integer, default=0, comment="重试次数")
    dispatch_status = Column(Enum(DispatchStatus), default=DispatchStatus.PUSHED, comment="派发状态")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联任务实例
    task_instance = relationship("TaskInstance", back_populates="sub_tasks")
    
    # 索引优化查询
    __table_args__ = (
        Index('idx_subtask_instance', 'instance_id'),
        Index('idx_subtask_status', 'status'),
    )
