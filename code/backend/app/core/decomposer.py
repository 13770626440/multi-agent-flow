"""
Decomposer - 动态任务分解器

负责将复杂任务通过 OpenMOSS 启动 Agent 进行自动分解，包括：
1. 创建分解任务到 OpenMOSS
2. 等待 Agent 完成分解（Event 驱动）
3. 解析 JSON 输出（容错重试）
4. 校验 JSON Schema
5. 校验 DAG 循环依赖
6. 注入元数据（required_skills 等）
"""
import json
import re
import asyncio
import logging
import networkx as nx
from typing import List, Dict, Any, Optional
from jsonschema import validate, ValidationError as JsonSchemaValidationError

from app.clients.openmoss_client import openmoss_client
from app.config import get_settings

# ARCH-006 修复：安全的 Skill Loader 导入
import importlib.util
from pathlib import Path
import os

def _safe_load_skill_loader():
    """安全加载 Skill Loader（ARCH-006 修复）"""
    from app.config import get_settings
    settings = get_settings()
    skills_dir = Path(settings.SKILLS_DIR).resolve()
    
    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate_paths = [
        os.path.join(_backend_dir, 'skills', 'agency-agent', 'loader.py'),
        os.path.join(os.path.dirname(_backend_dir), 'skills', 'agency-agent', 'loader.py')
    ]
    
    for _skills_path in candidate_paths:
        if os.path.exists(_skills_path):
            # 验证路径在 skills_dir 范围内
            resolved_path = Path(_skills_path).resolve()
            try:
                resolved_path.relative_to(skills_dir)
            except ValueError:
                raise SecurityError(f"Skill loader path {_skills_path} is outside SKILLS_DIR {skills_dir}")
            
            _loader_path = _skills_path
            break
    else:
        raise FileNotFoundError(f"Skill loader not found")
    
    _spec = importlib.util.spec_from_file_location("skill_loader", _loader_path)
    _loader_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_loader_module)
    return _loader_module.create_skill_loader

class SecurityError(Exception):
    pass

create_skill_loader = _safe_load_skill_loader()

logger = logging.getLogger(__name__)

settings = get_settings()


class JSONParseError(Exception):
    """JSON 解析错误"""
    pass


class SchemaValidationError(Exception):
    """Schema 校验错误"""
    pass


class DAGValidationError(Exception):
    """DAG 校验错误"""
    pass


class DecompositionFailed(Exception):
    """任务分解失败"""
    pass


class Decomposer:
    """动态任务分解器"""
    
    def __init__(self, timeout: Optional[int] = None):
        """
        初始化 Decomposer
        
        Args:
            timeout: 等待超时时间（秒），默认使用配置文件中的值
        """
        self.timeout = timeout or settings.DECOMPOSER_TIMEOUT
        self.completion_events: Dict[str, asyncio.Event] = {}
        self.completion_results: Dict[str, Dict] = {}
    
    async def decompose_task(
        self,
        task_def: Dict[str, Any],
        context: Dict[str, Any],
        parent_task_id: str
    ) -> List[Dict[str, Any]]:
        """
        执行动态任务分解（通过 OpenMOSS 启动 Agent）
        
        Args:
            task_def: YAML 中的任务定义
            context: 运行时上下文（包含前置任务输出）
            parent_task_id: 父任务 ID
        
        Returns:
            子任务列表
        
        Raises:
            DecompositionFailed: 分解失败
        """
        # 1. 构建完整指令（包含 Skills + Instruction）
        instruction = self._build_instruction(task_def, context)
        
        # 2. 创建分解任务到 OpenMOSS
        try:
            decompose_task = await openmoss_client.create_sub_task(
                task_id=parent_task_id,
                name=task_def.get("name", "任务分解"),
                assigned_agent=task_def.get("target_role", "tech-lead"),
                description=instruction,
                priority="high"
            )
            
            openmoss_id = decompose_task.get('id')
            logger.info(f"Decomposition task created in OpenMOSS: {openmoss_id}")
            
            # 3. 等待 Agent 完成
            result = await self._wait_for_completion(openmoss_id)
            
            # 4. 解析结果
            sub_tasks = self.parse_decomposition_result(
                result.get('output', ''),
                task_def
            )
            
            logger.info(f"Decomposition completed, created {len(sub_tasks)} sub-tasks")
            
            return sub_tasks
            
        except Exception as e:
            logger.error(f"Decomposition failed: {e}")
            raise DecompositionFailed(f"Decomposition failed: {e}")
    
    def _build_instruction(self, task_def: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        构建完整指令（包含 Skills 内容 + Instruction + Output Format）
        
        Args:
            task_def: YAML 中的任务定义
            context: 运行时上下文
        
        Returns:
            完整的指令文本（Markdown 格式）
        """
        parts = []
        
        # 1. 加载并注入 Required Skills 的实际内容
        required_skills = task_def.get("required_skills", [])
        target_role = task_def.get("target_role", "")
        
        if required_skills or target_role:
            skill_loader = create_skill_loader(
                skills_dir=settings.SKILLS_DIR,
                role_skill_map=settings.DEFAULT_ROLE_SKILL_MAP
            )
            
            # 优先使用显式声明的 required_skills，否则根据角色加载
            if required_skills:
                loaded_skills = skill_loader.load_skills(required_skills)
            elif target_role:
                loaded_skills = skill_loader.load_skills_for_role(target_role)
            else:
                loaded_skills = []
            
            if loaded_skills:
                parts.append("## Active Skills\n")
                for skill in loaded_skills:
                    parts.append(f"\n### Skill: {skill['name']}\n")
                    parts.append(skill['content'])
                logger.info(f"Loaded {len(loaded_skills)} skills for task: {[s['name'] for s in loaded_skills]}")
        
        # 2. Instruction（替换变量）
        instruction_template = task_def.get("execution_context", {}).get("instruction", "")
        instruction = self._render_template(instruction_template, context)
        if instruction:
            parts.append(f"\n## Instruction\n{instruction}\n")
        
        # 3. Output Format
        output_format = task_def.get("execution_context", {}).get("output_format", "json")
        parts.append(f"\n## Output Format\n{output_format}\n")
        
        # 4. Acceptance Criteria
        acceptance_criteria = task_def.get("acceptance_criteria", [])
        if acceptance_criteria:
            criteria_text = "\n".join([f"- {c}" for c in acceptance_criteria])
            parts.append(f"\n## Acceptance Criteria\n{criteria_text}\n")
        
        return "\n".join(parts)
    
    def _render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        渲染模板（替换变量）
        
        Args:
            template_str: 模板字符串
            context: 上下文变量
        
        Returns:
            渲染后的字符串
        """
        from jinja2 import Template
        template = Template(template_str)
        return template.render(**context)
    
    def parse_decomposition_result(self, output: str, task_def: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析 Agent 返回的分解结果
        
        Args:
            output: Agent 返回的文本
            task_def: YAML 中的任务定义（用于 Schema 校验）
        
        Returns:
            子任务列表
        
        Raises:
            JSONParseError: JSON 解析失败
            SchemaValidationError: Schema 校验失败
            DAGValidationError: DAG 校验失败
        """
        # 1. 解析 JSON
        sub_tasks = self._parse_json(output)
        
        # 2. Schema 校验
        output_schema = task_def.get("output_definition", {}).get("schema")
        if output_schema:
            self._validate_schema(sub_tasks, output_schema)
        
        # 3. DAG 校验
        self._validate_dag(sub_tasks)
        
        # 4. 注入元数据
        sub_tasks = self._inject_metadata(sub_tasks, task_def)
        
        return sub_tasks
    
    def _parse_json(self, response: str) -> List[Dict]:
        """
        解析 JSON（容错处理）
        
        Args:
            response: Agent 响应文本
        
        Returns:
            子任务列表
        
        Raises:
            JSONParseError: JSON 解析失败
        """
        json_str = None
        
        # 1. 尝试提取 Markdown 代码块
        match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # 2. 查找第一个 [ 和最后一个 ]
            start = response.find('[')
            end = response.rfind(']')
            if start != -1 and end != -1 and end > start:
                json_str = response[start:end+1]
        
        if json_str is None:
            raise JSONParseError("No JSON array found in response")
        
        # 3. 解析 JSON
        try:
            sub_tasks = json.loads(json_str)
            if not isinstance(sub_tasks, list):
                raise JSONParseError("Expected JSON array, got " + type(sub_tasks).__name__)
            return sub_tasks
        except json.JSONDecodeError as e:
            raise JSONParseError(f"Invalid JSON: {e}")
    
    def _validate_schema(self, sub_tasks: List[Dict], schema: Dict):
        """
        JSON Schema 校验（使用 jsonschema 库）
        
        Args:
            sub_tasks: 子任务列表
            schema: JSON Schema 定义
        
        Raises:
            SchemaValidationError: Schema 校验失败
        """
        # 构建完整 Schema
        if "type" in schema:
            # schema 已经是完整格式
            full_schema = schema
        else:
            # schema 只是 items 部分，需要包装
            full_schema = {
                "type": "array",
                "items": schema
            }
        
        try:
            validate(instance=sub_tasks, schema=full_schema)
        except JsonSchemaValidationError as e:
            raise SchemaValidationError(f"Schema validation failed: {e.message}")
    
    def _validate_dag(self, sub_tasks: List[Dict]):
        """
        DAG 循环依赖检测
        
        Args:
            sub_tasks: 子任务列表
        
        Raises:
            DAGValidationError: 检测到循环依赖
        """
        graph = nx.DiGraph()
        task_names = [task.get("name", f"task_{i}") for i, task in enumerate(sub_tasks)]
        
        # 构建图
        for i, task in enumerate(sub_tasks):
            task_name = task_names[i]
            graph.add_node(task_name)
            
            for dep in task.get("dependencies", []):
                if dep not in task_names:
                    raise DAGValidationError(
                        f"Task '{task_name}' depends on unknown task '{dep}'"
                    )
                graph.add_edge(dep, task_name)
        
        # 检测循环依赖
        if not nx.is_directed_acyclic_graph(graph):
            cycle = nx.find_cycle(graph)
            raise DAGValidationError(f"Circular dependency detected: {cycle}")
    
    def _inject_metadata(self, sub_tasks: List[Dict], task_def: Dict) -> List[Dict]:
        """
        注入元数据（required_skills 等）
        
        Args:
            sub_tasks: 子任务列表
            task_def: YAML 中的任务定义
        
        Returns:
            注入元数据后的子任务列表
        """
        for task in sub_tasks:
            # 继承父任务的 required_skills（如果没有指定）
            if "required_skills" not in task:
                task["required_skills"] = task_def.get("required_skills", [])
            
            # 继承父任务的 output_format
            if "output_format" not in task:
                task["output_format"] = task_def.get("execution_context", {}).get("output_format", "text")
        
        return sub_tasks
    
    async def _wait_for_completion(self, openmoss_id: str) -> Dict:
        """
        等待 Agent 完成任务（Event 驱动）
        
        Args:
            openmoss_id: OpenMOSS 子任务 ID
        
        Returns:
            任务结果（包含 output 字段）
        
        Raises:
            DecompositionFailed: 超时或任务失败
        """
        # 1. 创建 Event
        event = asyncio.Event()
        self.completion_events[openmoss_id] = event
        
        try:
            # 2. 等待 Event 被设置（带超时）
            await asyncio.wait_for(event.wait(), timeout=self.timeout)
            
            # 3. 获取结果
            result = self.completion_results.pop(openmoss_id, {})
            
            # 4. 检查是否失败
            if "error" in result:
                raise DecompositionFailed(result["error"])
            
            return result
            
        except asyncio.TimeoutError:
            raise DecompositionFailed(
                f"Decomposition task {openmoss_id} timeout after {self.timeout}s"
            )
        finally:
            # 5. 清理
            self.completion_events.pop(openmoss_id, None)
    
    def notify_completion(self, openmoss_id: str, result: Dict):
        """
        通知任务完成（由 SyncEngine 调用）
        
        Args:
            openmoss_id: OpenMOSS 子任务 ID
            result: 任务结果（包含 output 字段）
        """
        # 1. 保存结果
        self.completion_results[openmoss_id] = result
        
        # 2. 设置 Event（唤醒等待者）
        event = self.completion_events.get(openmoss_id)
        if event:
            event.set()
            logger.info(f"Notified completion for {openmoss_id}")
        else:
            logger.warning(f"No event found for {openmoss_id}, result saved but not notified")
    
    def notify_failure(self, openmoss_id: str, error: str):
        """
        通知任务失败（由 SyncEngine 调用）
        
        Args:
            openmoss_id: OpenMOSS 子任务 ID
            error: 错误信息
        """
        self.notify_completion(openmoss_id, {"error": error})
