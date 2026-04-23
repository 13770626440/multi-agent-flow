"""
模板管理模块 Pydantic Schema 定义

根据04-详细设计文档第9节 YAML Schema 定义，实现完整的数据模型。
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import networkx as nx


class OutputDefinition(BaseModel):
    """输出定义"""
    type: str = "file"
    format: Optional[str] = None
    path: str


class ExecutionContext(BaseModel):
    """执行上下文"""
    instruction: str
    input_mapping: Optional[Dict[str, str]] = Field(default_factory=dict)
    output_format: Optional[str] = None


class RetryPolicy(BaseModel):
    """重试策略"""
    max_retries: int = 2


class Control(BaseModel):
    """执行控制"""
    timeout: int = 300  # 秒
    retry_policy: Optional[RetryPolicy] = None


class TaskDefinition(BaseModel):
    """任务节点定义"""
    task_id: str
    name: str
    type: str = "fixed"  # fixed / dynamic / review
    dependencies: List[str] = Field(default_factory=list)
    
    # 角色与能力要求
    target_role: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    
    # 执行上下文
    execution_context: Optional[ExecutionContext] = None
    
    # 输出定义
    output_definition: Optional[OutputDefinition] = None
    
    # 验收标准
    acceptance_criteria: List[str] = Field(default_factory=list)
    
    # 执行控制
    control: Optional[Control] = None


class InputSchemaField(BaseModel):
    """输入字段定义"""
    type: str
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None


class TemplateSchema(BaseModel):
    """模板定义"""
    template_id: str
    version: str
    description: str
    input_schema: Optional[Dict[str, InputSchemaField]] = None
    tasks: List[TaskDefinition]
    
    @field_validator('tasks')
    @classmethod
    def validate_dag(cls, v: List[TaskDefinition]) -> List[TaskDefinition]:
        """校验 DAG 是否存在循环依赖"""
        graph = nx.DiGraph()
        task_ids = {t.task_id for t in v}
        
        for task in v:
            graph.add_node(task.task_id)
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Dependency '{dep}' not found in tasks")
                graph.add_edge(dep, task.task_id)
        
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Circular dependency detected in tasks")
        
        return v


class TemplateInstance(BaseModel):
    """任务实例（运行时快照）"""
    id: str
    template_id: str
    version: str
    inputs: Dict[str, Any]
    dag_snapshot: Dict[str, Any]  # 完整DAG快照
    status: str = "INITIALIZED"
    created_at: datetime
    updated_at: Optional[datetime] = None


class TemplateListItem(BaseModel):
    """模板列表项"""
    template_id: str
    version: str
    description: str
    task_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TemplateCreateRequest(BaseModel):
    """创建模板请求"""
    yaml_content: str


class TemplateInstantiateRequest(BaseModel):
    """实例化模板请求"""
    template_id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)