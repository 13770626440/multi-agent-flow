"""
任务管理 API 接口

提供任务创建、查询、子任务管理等功能。
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.task import TaskInstance, SubTaskRecord, TaskStatus, SubTaskStatus, DispatchStatus
from app.core.dag_engine import DAGEngine
from app.core.dispatcher import dispatcher

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


# --- Request/Response Models ---

class TaskCreateRequest(BaseModel):
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    template_id: Optional[str] = Field(None, description="关联的模板 ID")
    user_id: Optional[str] = Field(None, description="创建用户 ID")


class SubTaskCreateRequest(BaseModel):
    name: str = Field(..., description="子任务名称")
    role: str = Field(..., description="执行角色")
    instruction: str = Field(..., description="任务指令")
    dependencies: List[str] = Field(default_factory=list, description="依赖的子任务 ID")


class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    template_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubTaskResponse(BaseModel):
    id: str
    instance_id: str
    name: str
    role: str
    status: str
    dispatch_status: Optional[str]
    retry_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- API Endpoints ---

@router.post("/", response_model=TaskResponse)
async def create_task(request: TaskCreateRequest, db: AsyncSession = Depends(get_db)):
    """创建任务实例"""
    task_id = str(uuid.uuid4())
    
    task = TaskInstance(
        id=task_id,
        name=request.name,
        description=request.description,
        template_id=request.template_id,
        user_id=request.user_id,
        status=TaskStatus.PENDING
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return task


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """查询任务列表"""
    query = select(TaskInstance)
    
    if status:
        query = query.where(TaskInstance.status == status)
    
    query = query.offset(skip).limit(limit).order_by(TaskInstance.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """获取任务详情"""
    result = await db.execute(select(TaskInstance).where(TaskInstance.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.get("/{task_id}/sub-tasks", response_model=List[SubTaskResponse])
async def list_sub_tasks(task_id: str, db: AsyncSession = Depends(get_db)):
    """获取子任务列表"""
    result = await db.execute(
        select(SubTaskRecord).where(SubTaskRecord.instance_id == task_id)
    )
    sub_tasks = result.scalars().all()
    
    return sub_tasks


@router.post("/{task_id}/sub-tasks", response_model=SubTaskResponse)
async def create_sub_task(task_id: str, request: SubTaskCreateRequest, db: AsyncSession = Depends(get_db)):
    """创建并派发子任务"""
    # 验证主任务存在
    result = await db.execute(select(TaskInstance).where(TaskInstance.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    sub_task_id = str(uuid.uuid4())
    conversation_id = f"task_{task_id}_sub_{sub_task_id[:8]}"
    
    sub_task = SubTaskRecord(
        id=sub_task_id,
        instance_id=task_id,
        name=request.name,
        role=request.role,
        instruction=request.instruction,
        dependencies=request.dependencies,
        conversation_id=conversation_id,
        status=SubTaskStatus.ASSIGNED,
        dispatch_status=DispatchStatus.PUSHED
    )
    
    db.add(sub_task)
    await db.commit()
    await db.refresh(sub_task)
    
    # 派发任务
    try:
        dispatch_result = await dispatcher.dispatch_task(
            sub_task_id=sub_task_id,
            openmoss_id="",  # TODO: 创建 OpenMOSS 子任务后获取 ID
            role=request.role,
            instruction=request.instruction,
            conversation_id=conversation_id
        )
        sub_task.dispatch_status = dispatch_result["status"]
        await db.commit()
    except Exception as e:
        # 派发失败，降级为 Pull 模式
        sub_task.dispatch_status = DispatchStatus.PENDING_PULL
        await db.commit()
    
    return sub_task


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """取消任务"""
    result = await db.execute(select(TaskInstance).where(TaskInstance.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = TaskStatus.CANCELLED
    await db.commit()
    
    return {"message": f"Task {task_id} cancelled"}
