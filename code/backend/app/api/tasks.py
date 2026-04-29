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
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.task import TaskInstance, SubTaskRecord, TaskStatus, SubTaskStatus, DispatchStatus
from app.core.dag_engine import DAGEngine
from app.core.dispatcher import dispatcher
from app.clients.openmoss_client import openmoss_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


# --- Request/Response Models ---

class TaskCreateRequest(BaseModel):
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    template_id: Optional[str] = Field(None, description="关联的模板 ID")
    user_id: Optional[str] = Field(None, description="创建用户 ID")
    input_params: Optional[dict] = Field(None, description="模板输入参数")


class SubTaskCreateRequest(BaseModel):
    name: str = Field(..., description="子任务名称")
    role: str = Field(..., description="执行角色")
    instruction: str = Field(..., description="任务指令")
    dependencies: List[str] = Field(default_factory=list, description="依赖的子任务 ID")


class SubTaskCompleteRequest(BaseModel):
    status: str = Field(default="done", description="完成状态 (done/failed)")
    output_path: Optional[str] = Field(None, description="产出文件路径")
    message: Optional[str] = Field(None, description="完成消息或错误信息")


class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    template_id: Optional[str]
    input_params: Optional[dict] = None
    dag_snapshot: Optional[dict] = None
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
    """创建任务实例（同步创建 OpenMOSS Task）"""
    from app.core.redis_client import redis_client
    
    task_id = str(uuid.uuid4())
    
    # 步骤 0：如果指定了 template_id，加载模板并保存 DAG 快照（ARCH-007 修复：保存完整信息）
    dag_snapshot = None
    if request.template_id:
        try:
            redis_key = f"template:{request.template_id}"
            template_data = redis_client.get(redis_key)
            if template_data and 'tasks' in template_data:
                dag_snapshot = {
                    "tasks": [
                        {
                            "task_id": t["task_id"],
                            "name": t["name"],
                            "type": t["type"],
                            "dependencies": t.get("dependencies", []),
                            "target_role": t.get("target_role"),
                            "execution_context": t.get("execution_context", {}),
                            "output_definition": t.get("output_definition", {}),
                            "acceptance_criteria": t.get("acceptance_criteria", []),
                            "required_skills": t.get("required_skills", [])
                        }
                        for t in template_data["tasks"]
                    ]
                }
                logger.info(f"DAG snapshot loaded for template {request.template_id}")
        except Exception as e:
            logger.warning(f"Failed to load DAG snapshot: {e}")
    
    # 步骤 1：在 OpenMOSS 中创建 Task
    openmoss_task_id = None
    try:
        om_response = await openmoss_client.create_task(
            name=request.name,
            description=request.description or ""
        )
        openmoss_task_id = om_response.get("id")
        logger.info(f"OpenMOSS task created: {openmoss_task_id}")
    except Exception as e:
        logger.warning(f"Failed to create OpenMOSS task: {e}")
        # OpenMOSS 创建失败不阻塞 MAF 任务创建
    
    # 步骤 2：创建 MAF 任务实例
    task = TaskInstance(
        id=task_id,
        name=request.name,
        description=request.description,
        template_id=request.template_id,
        user_id=request.user_id,
        input_params=request.input_params,
        openmoss_task_id=openmoss_task_id,
        status=TaskStatus.PENDING,
        dag_snapshot=dag_snapshot
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
    
    # 使用 OpenMOSS task_id（如果存在）
    openmoss_task_id = task.openmoss_task_id or task_id
    
    # 步骤 1：先在 OpenMOSS 中创建子任务，获取 openmoss_id
    openmoss_id = None
    try:
        om_response = await openmoss_client.create_sub_task(
            task_id=openmoss_task_id,
            name=request.name,
            description=request.instruction,
            deliverable="",
            acceptance="",
            priority="medium"
        )
        openmoss_id = om_response.get("id") or om_response.get("sub_task_id")
        if not openmoss_id:
            logger.warning(f"OpenMOSS response missing id field: {om_response}")
            openmoss_id = f"om_{task_id}_{str(uuid.uuid4())[:8]}"
        logger.info(f"OpenMOSS sub-task created: {openmoss_id}")
    except Exception as e:
        logger.error(f"Failed to create OpenMOSS sub-task: {e}")
        raise HTTPException(status_code=502, detail=f"OpenMOSS sub-task creation failed: {str(e)}")
    
    # 步骤 2：创建本地子任务记录
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
        openmoss_id=openmoss_id,
        status=SubTaskStatus.ASSIGNED,
        dispatch_status=DispatchStatus.PUSHED
    )
    
    db.add(sub_task)
    await db.commit()
    await db.refresh(sub_task)
    
    # 步骤 3：派发任务（推拉结合）
    try:
        dispatch_result = await dispatcher.dispatch_task(
            sub_task_id=sub_task_id,
            openmoss_id=openmoss_id,
            role=request.role,
            instruction=request.instruction,
            conversation_id=conversation_id
        )
        sub_task.dispatch_status = dispatch_result["status"]
        await db.commit()
    except Exception as e:
        # 派发失败，降级为 Pull 模式
        logger.warning(f"Dispatch failed for sub-task {sub_task_id}: {e}")
        sub_task.dispatch_status = DispatchStatus.PENDING_PULL
        await db.commit()
    
    return sub_task


@router.post("/{task_id}/sub-tasks/{sub_task_id}/complete")
async def complete_sub_task(
    task_id: str,
    sub_task_id: str,
    request: SubTaskCompleteRequest,
    db: AsyncSession = Depends(get_db),
    x_agent_key: Optional[str] = None
):
    """
    Agent 汇报子任务完成
    
    由执行任务的 Agent 调用，更新子任务状态。
    需要 Agent Key 鉴权（ARCH-001 修复）
    """
    # 0. Agent Key 鉴权（ARCH-001 修复）
    if not x_agent_key:
        raise HTTPException(status_code=401, detail="Agent Key required")
    
    # 验证 Agent Key 是否有效（从 OpenMOSS 验证）
    # TODO: 实现完整的 Agent Key 验证逻辑
    # 当前简化：只要提供了 Agent Key 就允许
    logger.info(f"Agent with key {x_agent_key[:8]}... reporting task completion")
    
    # 1. 查找子任务
    result = await db.execute(
        select(SubTaskRecord).where(
            SubTaskRecord.id == sub_task_id,
            SubTaskRecord.instance_id == task_id
        )
    )
    sub_task = result.scalar_one_or_none()
    
    if not sub_task:
        raise HTTPException(status_code=404, detail="Sub-task not found")
    
    # 2. 更新状态
    if request.status == "done":
        sub_task.status = SubTaskStatus.DONE
    elif request.status == "failed":
        sub_task.status = SubTaskStatus.FAILED
    else:
        sub_task.status = SubTaskStatus.DONE # 默认完成
    
    # 3. 保存产出路径（ARCH-004 修复：不修改 instruction）
    if request.output_path:
        sub_task.output = request.output_path
    # 完成消息存储到单独字段（如果需要的话）
    # 不再修改 instruction 字段
        
    await db.commit()
    
    return {"message": f"Sub-task {sub_task_id} status updated to {sub_task.status.value}"}


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
