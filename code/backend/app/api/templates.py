"""
模板管理 API 接口

提供模板 CRUD 操作。
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List
import yaml
import logging
from app.schemas.template import (
    TemplateSchema,
    TemplateListItem,
    TemplateCreateRequest,
    TemplateInstantiateRequest,
    TemplateInstance
)
from app.core.template_loader import TemplateLoader
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# API限流配置：每分钟最多100次请求
limiter = Limiter(key_func=get_remote_address)

# 全局模板加载器实例
_template_loader: TemplateLoader = None


def get_template_loader() -> TemplateLoader:
    """获取模板加载器实例"""
    global _template_loader
    if _template_loader is None:
        settings = get_settings()
        _template_loader = TemplateLoader(settings.TEMPLATE_DIR)
        _template_loader.start()
    return _template_loader


@router.get("/", response_model=List[TemplateListItem])
@limiter.limit("100/minute")
async def list_templates(request: Request, loader: TemplateLoader = Depends(get_template_loader)):
    """
    获取模板列表
    
    返回所有已加载的模板ID及其基本信息。
    
    限流：每分钟最多100次请求。
    """
    template_ids = loader.list_templates()
    items = []
    for tid in template_ids:
        template = loader.get_template(tid)
        if template:
            items.append(TemplateListItem(
                template_id=template.template_id,
                version=template.version,
                description=template.description,
                task_count=len(template.tasks)
            ))
    return items


@router.get("/{template_id}", response_model=TemplateSchema)
@limiter.limit("100/minute")
async def get_template(request: Request, template_id: str, loader: TemplateLoader = Depends(get_template_loader)):
    """
    获取单个模板详情
    
    根据template_id返回完整的模板定义，包括所有任务节点和DAG结构。
    
    参数：
    - template_id: 模板唯一标识
    
    返回：完整的TemplateSchema对象
    
    错误：
    - 404: 模板不存在
    """
    template = loader.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return template


@router.post("/", response_model=TemplateSchema)
@limiter.limit("20/minute")
async def create_template(
    http_request: Request,
    request: TemplateCreateRequest,
    loader: TemplateLoader = Depends(get_template_loader)
):
    """
    创建新模板
    
    通过YAML内容创建新的任务模板。YAML必须符合TemplateSchema定义。
    
    请求体：
    - yaml_content: YAML格式的模板定义
    
    返回：创建成功的TemplateSchema对象
    
    错误：
    - 400: YAML格式错误或校验失败
    - 409: 模板ID已存在
    - 500: 存储失败
    
    限流：每分钟最多20次请求（创建操作较重）
    """
    try:
        # 解析 YAML 内容
        data = yaml.safe_load(request.yaml_content)
        if not data:
            raise HTTPException(status_code=400, detail="YAML content is empty")
        
        # 校验模板
        template = TemplateSchema(**data)
        
        # 检查是否已存在
        existing = loader.get_template(template.template_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Template '{template.template_id}' already exists"
            )
        
        # 存入 Redis
        redis_key = f"template:{template.template_id}"
        from app.core.redis_client import redis_client
        if not redis_client.set(redis_key, template.model_dump()):
            raise HTTPException(status_code=500, detail="Failed to save template")
        
        loader._templates[template.template_id] = template
        logger.info(f"Template {template.template_id} created")
        return template
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML syntax error: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Template validation error: {e}")


@router.delete("/{template_id}")
@limiter.limit("50/minute")
async def delete_template(
    request: Request,
    template_id: str,
    loader: TemplateLoader = Depends(get_template_loader)
):
    """
    删除模板
    
    根据template_id删除模板。删除后模板将从Redis缓存中移除。
    
    参数：
    - template_id: 模板唯一标识
    
    返回：删除成功消息
    
    错误：
    - 404: 模板不存在
    - 500: 删除失败
    
    限流：每分钟最多50次请求
    """
    template = loader.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    
    if loader.delete_template(template_id):
        return {"message": f"Template '{template_id}' deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete template")


@router.post("/{template_id}/instantiate", response_model=TemplateInstance)
@limiter.limit("30/minute")
async def instantiate_template(
    http_request: Request,
    template_id: str,
    request: TemplateInstantiateRequest,
    loader: TemplateLoader = Depends(get_template_loader)
):
    """
    实例化模板（创建任务实例）
    
    根据模板定义创建任务实例，生成DAG快照并存入数据库。
    
    参数：
    - template_id: 模板唯一标识
    
    请求体：
    - inputs: 模板输入参数（可选）
    
    返回：TemplateInstance对象，包含实例ID和DAG快照
    
    错误：
    - 404: 模板不存在
    
    限流：每分钟最多30次请求
    
    注意：完整实例化逻辑将在MVP-02-T03任务管理模块实现
    """
    template = loader.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    
    # TODO: 完整实例化逻辑将在 MVP-02-T03 任务管理模块实现
    # 当前仅返回模拟数据用于测试
    
    from datetime import datetime
    from uuid import uuid4
    
    instance = TemplateInstance(
        id=str(uuid4()),
        template_id=template_id,
        version=template.version,
        inputs=request.inputs,
        dag_snapshot=template.model_dump(),
        status="INITIALIZED",
        created_at=datetime.now()
    )
    
    logger.info(f"Template {template_id} instantiated as {instance.id}")
    return instance