"""
Decomposer 单元测试

测试动态任务分解器的核心功能：
1. JSON 解析（容错处理）
2. Schema 校验
3. DAG 循环依赖检测
4. 元数据注入
"""
import pytest
import json
from app.core.decomposer import (
    Decomposer,
    JSONParseError,
    SchemaValidationError,
    DAGValidationError
)


class TestDecomposer:
    """Decomposer 测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.decomposer = Decomposer()
    
    # --- JSON 解析测试 ---
    
    def test_parse_json_valid(self):
        """测试有效 JSON 解析"""
        response = json.dumps([
            {"name": "task1", "role": "backend", "dependencies": []},
            {"name": "task2", "role": "frontend", "dependencies": ["task1"]}
        ])
        
        result = self.decomposer._parse_json(response)
        
        assert len(result) == 2
        assert result[0]["name"] == "task1"
        assert result[1]["dependencies"] == ["task1"]
    
    def test_parse_json_markdown_code_block(self):
        """测试 Markdown 代码块提取"""
        response = """```json
[
  {"name": "task1", "role": "backend", "dependencies": []}
]
```"""
        
        result = self.decomposer._parse_json(response)
        
        assert len(result) == 1
        assert result[0]["name"] == "task1"
    
    def test_parse_json_no_array_should_fail(self):
        """测试无 JSON 数组应失败"""
        response = "这是一个普通文本，没有 JSON"
        
        with pytest.raises(JSONParseError, match="No JSON array found"):
            self.decomposer._parse_json(response)
    
    def test_parse_json_invalid_should_fail(self):
        """测试无效 JSON 应失败"""
        response = "[{invalid json}]"
        
        with pytest.raises(JSONParseError, match="Invalid JSON"):
            self.decomposer._parse_json(response)
    
    # --- Schema 校验测试 ---
    
    def test_validate_schema_valid(self):
        """测试有效 Schema 校验"""
        sub_tasks = [
            {"name": "task1", "role": "backend", "instruction": "do something"}
        ]
        schema = {
            "items": {
                "required": ["name", "role"],
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "dependencies": {"type": "array"}
                }
            }
        }
        
        # 不应抛出异常
        self.decomposer._validate_schema(sub_tasks, schema)
    
    def test_validate_schema_missing_required_should_fail(self):
        """测试缺少必填字段应失败"""
        sub_tasks = [
            {"role": "backend"}  # 缺少 name
        ]
        schema = {
            "required": ["name", "role"]
        }
        
        with pytest.raises(SchemaValidationError):
            self.decomposer._validate_schema(sub_tasks, schema)
    
    # --- DAG 校验测试 ---
    
    def test_validate_dag_no_cycle(self):
        """测试 DAG 无循环依赖"""
        sub_tasks = [
            {"name": "task1", "dependencies": []},
            {"name": "task2", "dependencies": ["task1"]},
            {"name": "task3", "dependencies": ["task2"]}
        ]
        
        # 不应抛出异常
        self.decomposer._validate_dag(sub_tasks)
    
    def test_validate_dag_with_cycle_should_fail(self):
        """测试 DAG 循环依赖应失败"""
        sub_tasks = [
            {"name": "task1", "dependencies": ["task3"]},
            {"name": "task2", "dependencies": ["task1"]},
            {"name": "task3", "dependencies": ["task2"]}
        ]
        
        with pytest.raises(DAGValidationError, match="Circular dependency"):
            self.decomposer._validate_dag(sub_tasks)
    
    def test_validate_dag_unknown_dependency_should_fail(self):
        """测试依赖未知任务应失败"""
        sub_tasks = [
            {"name": "task1", "dependencies": ["unknown_task"]}
        ]
        
        with pytest.raises(DAGValidationError, match="unknown task"):
            self.decomposer._validate_dag(sub_tasks)
    
    # --- 元数据注入测试 ---
    
    def test_inject_metadata(self):
        """测试元数据注入"""
        sub_tasks = [
            {"name": "task1", "role": "backend"}
        ]
        task_def = {
            "required_skills": ["skill1", "skill2"],
            "execution_context": {"output_format": "json"}
        }
        
        result = self.decomposer._inject_metadata(sub_tasks, task_def)
        
        assert result[0]["required_skills"] == ["skill1", "skill2"]
        assert result[0]["output_format"] == "json"
    
    def test_inject_metadata_should_not_override_existing(self):
        """测试元数据注入不应覆盖已有值"""
        sub_tasks = [
            {"name": "task1", "role": "backend", "required_skills": ["custom-skill"]}
        ]
        task_def = {
            "required_skills": ["skill1", "skill2"]
        }
        
        result = self.decomposer._inject_metadata(sub_tasks, task_def)
        
        # 应保留原有值
        assert result[0]["required_skills"] == ["custom-skill"]
    
    # --- 边界条件测试 ---
    
    def test_parse_json_large_response(self):
        """测试超大 JSON 响应"""
        # 生成 100 个子任务
        tasks = [{"name": f"task_{i}", "role": "backend", "dependencies": []} for i in range(100)]
        response = json.dumps(tasks)
        
        result = self.decomposer._parse_json(response)
        
        assert len(result) == 100
    
    def test_parse_json_nested_dependencies(self):
        """测试深层嵌套依赖"""
        response = json.dumps([
            {"name": "task_1", "role": "backend", "dependencies": []},
            {"name": "task_2", "role": "backend", "dependencies": ["task_1"]},
            {"name": "task_3", "role": "backend", "dependencies": ["task_2"]},
            {"name": "task_4", "role": "backend", "dependencies": ["task_3"]},
            {"name": "task_5", "role": "backend", "dependencies": ["task_4"]}
        ])
        
        result = self.decomposer._parse_json(response)
        self.decomposer._validate_dag(result)
        
        assert len(result) == 5
    
    def test_validate_schema_with_jsonschema(self):
        """测试 jsonschema 完整校验"""
        sub_tasks = [
            {"name": "task1", "role": "backend", "instruction": "do something"}
        ]
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "role"],
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string", "enum": ["backend", "frontend", "database"]},
                    "dependencies": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
        
        # 应通过校验
        self.decomposer._validate_schema(sub_tasks, schema)
    
    def test_validate_schema_invalid_role(self):
        """测试无效 role 应失败"""
        sub_tasks = [
            {"name": "task1", "role": "invalid_role"}
        ]
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "enum": ["backend", "frontend", "database"]}
                }
            }
        }
        
        with pytest.raises(SchemaValidationError):
            self.decomposer._validate_schema(sub_tasks, schema)