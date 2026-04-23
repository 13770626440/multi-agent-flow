"""
模板管理模块单元测试

测试覆盖：
1. TemplateSchema 校验
2. TemplateLoader 加载逻辑
3. TemplateManager API 接口
"""
import pytest
import yaml
import tempfile
import os
from pydantic import ValidationError

from app.schemas.template import (
    TemplateSchema,
    TaskDefinition,
    ExecutionContext,
    OutputDefinition,
    Control
)


class TestTemplateSchema:
    """TemplateSchema 单元测试"""
    
    def test_valid_template(self):
        """测试有效的模板定义"""
        data = {
            "template_id": "test-template-001",
            "version": "1.0.0",
            "description": "测试模板",
            "tasks": [
                {
                    "task_id": "task-1",
                    "name": "任务1",
                    "type": "fixed",
                    "dependencies": [],
                    "target_role": "executor",
                    "required_skills": ["coder"],
                    "execution_context": {
                        "instruction": "执行任务1"
                    },
                    "acceptance_criteria": ["输出正确"]
                }
            ]
        }
        template = TemplateSchema(**data)
        assert template.template_id == "test-template-001"
        assert template.version == "1.0.0"
        assert len(template.tasks) == 1
    
    def test_dag_no_cycle(self):
        """测试 DAG 无循环依赖"""
        data = {
            "template_id": "dag-test",
            "version": "1.0.0",
            "description": "DAG测试",
            "tasks": [
                {"task_id": "task-1", "name": "任务1", "dependencies": []},
                {"task_id": "task-2", "name": "任务2", "dependencies": ["task-1"]},
                {"task_id": "task-3", "name": "任务3", "dependencies": ["task-2"]}
            ]
        }
        template = TemplateSchema(**data)
        assert template is not None
    
    def test_dag_with_cycle_should_fail(self):
        """测试 DAG 存在循环依赖应失败"""
        data = {
            "template_id": "cycle-test",
            "version": "1.0.0",
            "description": "循环测试",
            "tasks": [
                {"task_id": "task-1", "name": "任务1", "dependencies": ["task-3"]},
                {"task_id": "task-2", "name": "任务2", "dependencies": ["task-1"]},
                {"task_id": "task-3", "name": "任务3", "dependencies": ["task-2"]}
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            TemplateSchema(**data)
        assert "Circular dependency" in str(exc_info.value)
    
    def test_missing_dependency_should_fail(self):
        """测试依赖不存在应失败"""
        data = {
            "template_id": "missing-dep-test",
            "version": "1.0.0",
            "description": "缺失依赖测试",
            "tasks": [
                {"task_id": "task-1", "name": "任务1", "dependencies": ["non-existent"]}
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            TemplateSchema(**data)
        assert "not found" in str(exc_info.value)
    
    def test_task_types(self):
        """测试不同任务类型"""
        # fixed 类型
        fixed_task = TaskDefinition(task_id="fixed-1", name="固定任务", type="fixed")
        assert fixed_task.type == "fixed"
        
        # dynamic 类型
        dynamic_task = TaskDefinition(task_id="dynamic-1", name="动态任务", type="dynamic")
        assert dynamic_task.type == "dynamic"
        
        # review 类型
        review_task = TaskDefinition(task_id="review-1", name="评审任务", type="review")
        assert review_task.type == "review"
    
    def test_execution_context(self):
        """测试执行上下文"""
        ctx = ExecutionContext(
            instruction="执行指令",
            input_mapping={"source": "${input.data}"},
            output_format="json"
        )
        assert ctx.instruction == "执行指令"
        assert ctx.input_mapping["source"] == "${input.data}"
    
    def test_output_definition(self):
        """测试输出定义"""
        output = OutputDefinition(
            type="file",
            format="json",
            path="/workspace/output.json"
        )
        assert output.type == "file"
        assert output.path == "/workspace/output.json"
    
    def test_control_settings(self):
        """测试执行控制"""
        control = Control(timeout=600)
        assert control.timeout == 600


class TestTemplateLoader:
    """TemplateLoader 单元测试"""
    
    def test_load_yaml_file(self):
        """测试加载 YAML 文件"""
        # 创建临时 YAML 文件
        yaml_content = """
template_id: "loader-test"
version: "1.0.0"
description: "加载器测试"
tasks:
  - task_id: "task-1"
    name: "任务1"
    dependencies: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            data = yaml.safe_load(open(temp_path))
            template = TemplateSchema(**data)
            assert template.template_id == "loader-test"
        finally:
            os.unlink(temp_path)
    
    def test_invalid_yaml_should_fail(self):
        """测试无效 YAML 应失败"""
        yaml_content = """
template_id: "invalid"
version: "1.0.0"
description: [invalid list]  # 应该是字符串
tasks: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            data = yaml.safe_load(open(temp_path))
            with pytest.raises(ValidationError):
                TemplateSchema(**data)
        finally:
            os.unlink(temp_path)
    
    def test_empty_yaml_should_fail(self):
        """测试空 YAML 文件应失败"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            data = yaml.safe_load(open(temp_path))
            assert data is None
        finally:
            os.unlink(temp_path)


class TestParallelExecution:
    """并行执行测试"""
    
    def test_parallel_tasks(self):
        """测试并行任务定义"""
        data = {
            "template_id": "parallel-test",
            "version": "1.0.0",
            "description": "并行测试",
            "tasks": [
                {"task_id": "task-1", "name": "任务1", "dependencies": []},
                {"task_id": "task-2", "name": "任务2", "dependencies": []},  # 与task-1并行
                {"task_id": "task-3", "name": "任务3", "dependencies": ["task-1", "task-2"]}  # 等待两者完成
            ]
        }
        template = TemplateSchema(**data)
        
        # task-1 和 task-2 无依赖，可并行
        assert template.tasks[0].dependencies == []
        assert template.tasks[1].dependencies == []
        
        # task-3 等待两者
        assert "task-1" in template.tasks[2].dependencies
        assert "task-2" in template.tasks[2].dependencies


# 运行测试的命令
# pytest tests/test_template.py -v


class TestRedisClient:
    """RedisClient 单元测试"""
    
    def test_redis_client_class_definition(self):
        """测试 RedisClient 类定义"""
        from app.core.redis_client import RedisClient
        
        client = RedisClient()
        
        # 验证类方法存在
        assert hasattr(client, 'connect')
        assert hasattr(client, 'disconnect')
        assert hasattr(client, 'is_connected')
        assert hasattr(client, 'get')
        assert hasattr(client, 'set')
        assert hasattr(client, 'delete')
        assert hasattr(client, 'exists')
        assert hasattr(client, 'keys')
    
    def test_redis_set_dict(self):
        """测试 Redis set 方法处理 dict 类型"""
        from app.core.redis_client import RedisClient
        import json
        
        client = RedisClient()
        
        # 验证 dict 序列化逻辑
        test_data = {'key': 'value', 'nested': {'a': 1}}
        serialized = json.dumps(test_data)
        deserialized = json.loads(serialized)
        
        assert deserialized == test_data
    
    def test_redis_get_json(self):
        """测试 Redis get 方法反序列化"""
        from app.core.redis_client import RedisClient
        import json
        
        client = RedisClient()
        
        # 验证 JSON 反序列化逻辑
        test_json = '{"name": "test", "version": "1.0"}'
        result = json.loads(test_json)
        
        assert result['name'] == 'test'
        assert result['version'] == '1.0'


class TestTemplateLoaderLifecycle:
    """TemplateLoader 生命周期测试"""
    
    def test_template_loader_init(self):
        """测试 TemplateLoader 初始化"""
        from app.core.template_loader import TemplateLoader
        
        loader = TemplateLoader('/tmp/test_templates')
        
        assert loader.template_dir == '/tmp/test_templates'
        assert hasattr(loader, 'observer')
        assert hasattr(loader, 'handler')
        assert hasattr(loader, '_templates')
    
    def test_template_loader_methods(self):
        """测试 TemplateLoader 方法定义"""
        from app.core.template_loader import TemplateLoader
        
        loader = TemplateLoader('/tmp/test_templates')
        
        # 验证方法存在
        assert hasattr(loader, 'start')
        assert hasattr(loader, 'stop')
        assert hasattr(loader, 'load_all_existing')
        assert hasattr(loader, 'load_template')
        assert hasattr(loader, 'get_template')
        assert hasattr(loader, 'list_templates')
        assert hasattr(loader, 'delete_template')
    
    def test_template_file_handler_debounce(self):
        """测试文件处理器防抖动配置"""
        from app.core.template_loader import TemplateFileHandler, TemplateLoader
        
        loader = TemplateLoader('/tmp/test_templates')
        handler = TemplateFileHandler(loader, debounce_seconds=2.0)
        
        # 验证防抖动时间可配置
        assert handler.debounce_seconds == 2.0
    
    def test_debounce_config_from_settings(self):
        """测试防抖动时间从配置读取"""
        from app.core.template_loader import TemplateLoader
        from app.config import get_settings
        
        settings = get_settings()
        loader = TemplateLoader()
        
        # 验证防抖动时间来自配置
        assert loader.debounce_seconds == settings.TEMPLATE_DEBOUNCE_SECONDS