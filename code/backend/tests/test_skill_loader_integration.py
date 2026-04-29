"""
test_skill_loader_integration.py - SkillLoader 集成测试

验证：
1. SkillLoader 能正确加载角色对应的 Skills
2. SkillLoader 能发现所有可用 Skills
3. SkillLoader 能构建包含 Skill 内容的 System Prompt
4. agent_provisioner 能在入职包中注入 Skills
5. decomposer 能在指令中注入 Skills
6. sub_task_creator 能在 description 中注入 Skills
"""
import os
import sys
import pytest
import importlib.util
from unittest.mock import patch, MagicMock, AsyncMock

# 添加 backend 目录到 sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 使用 importlib 导入带连字符的模块
_loader_spec = importlib.util.spec_from_file_location(
    "skill_loader",
    os.path.join(backend_dir, "skills", "agency-agent", "loader.py")
)
_skill_loader_module = importlib.util.module_from_spec(_loader_spec)
_loader_spec.loader.exec_module(_skill_loader_module)
SkillLoader = _skill_loader_module.SkillLoader
get_skill_loader = _skill_loader_module.get_skill_loader


class TestSkillLoaderIntegration:
    """SkillLoader 集成测试"""
    
    @pytest.fixture
    def skills_dir(self, tmp_path):
        """创建临时 Skills 目录"""
        # 创建测试 Skills
        skills = {
            "test-skill-1": """---
name: test-skill-1
description: 测试 Skill 1
dependencies: []
---

# Test Skill 1

这是测试 Skill 1 的内容。
""",
            "test-skill-2": """---
name: test-skill-2
description: 测试 Skill 2
dependencies: []
---

# Test Skill 2

这是测试 Skill 2 的内容。
""",
            "agency-agent": """---
name: agency-agent
description: 基座 Skill
dependencies: []
---

# Agency Agent

你是任务执行 Agent。
"""
        }
        
        for skill_name, content in skills.items():
            skill_dir = tmp_path / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(content, encoding='utf-8')
        
        return str(tmp_path)
    
    @pytest.fixture
    def role_skill_map(self):
        """角色能力映射"""
        return {
            "product-manager": ["test-skill-1"],
            "tech-lead": ["test-skill-1", "test-skill-2"],
            "executor": ["agency-agent"],
        }
    
    @pytest.fixture
    def loader(self, skills_dir, role_skill_map):
        """创建 SkillLoader 实例"""
        return SkillLoader(skills_dir, role_skill_map)
    
    def test_load_skills_for_role(self, loader):
        """测试：根据角色加载 Skills"""
        # 测试 product-manager 角色
        skills = loader.load_skills_for_role("product-manager")
        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill-1"
        assert "测试 Skill 1" in skills[0]["content"]
        
        # 测试 tech-lead 角色
        skills = loader.load_skills_for_role("tech-lead")
        assert len(skills) == 2
        assert [s["name"] for s in skills] == ["test-skill-1", "test-skill-2"]
    
    def test_discover_all_skills(self, loader, skills_dir):
        """测试：发现所有可用 Skills"""
        skills = loader.discover_all_skills()
        assert len(skills) == 3
        assert "test-skill-1" in skills
        assert "test-skill-2" in skills
        assert "agency-agent" in skills
    
    def test_build_system_prompt(self, loader):
        """测试：构建 System Prompt"""
        skills = loader.load_skills_for_role("product-manager")
        prompt = loader.build_system_prompt(skills, "请分析用户需求")
        
        assert "# Agency Agent" in prompt
        assert "## Active Skill: test-skill-1" in prompt
        assert "测试 Skill 1" in prompt
        assert "## Current Task" in prompt
        assert "请分析用户需求" in prompt
    
    def test_get_skills_for_role_default(self, loader):
        """测试：未配置角色时返回默认 Skill"""
        skills = loader.get_skills_for_role("unknown-role")
        assert skills == ["agency-agent"]
    
    def test_load_skills_missing(self, loader):
        """测试：加载不存在的 Skill"""
        skills = loader.load_skills(["non-existent-skill"])
        assert len(skills) == 0
    
    def test_get_skill_loader_singleton(self, skills_dir, role_skill_map):
        """测试：全局单例模式"""
        # 重置全局单例
        _skill_loader_module._skill_loader = None
        
        loader1 = get_skill_loader(skills_dir, role_skill_map)
        loader2 = get_skill_loader(skills_dir, role_skill_map)
        
        assert loader1 is loader2


class TestDecomposerSkillInjection:
    """Decomposer Skill 注入测试"""
    
    @pytest.fixture
    def skills_dir(self, tmp_path):
        """创建临时 Skills 目录"""
        skill_dir = tmp_path / "decomposer-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: decomposer-skill
description: 任务分解 Skill
---

# Decomposer Skill

你是一个任务分解专家。
""", encoding='utf-8')
        return str(tmp_path)
    
    @patch('app.core.decomposer.settings')
    def test_build_instruction_with_skills(self, mock_settings, skills_dir):
        """测试：Decomposer 构建指令时注入 Skills"""
        from app.core.decomposer import Decomposer
        
        mock_settings.SKILLS_DIR = skills_dir
        mock_settings.DEFAULT_ROLE_SKILL_MAP = {
            "tech-lead": ["decomposer-skill"]
        }
        
        decomposer = Decomposer()
        task_def = {
            "target_role": "tech-lead",
            "required_skills": ["decomposer-skill"],
            "execution_context": {
                "instruction": "请分解任务",
                "output_format": "json"
            }
        }
        
        instruction = decomposer._build_instruction(task_def, {})
        
        assert "## Active Skills" in instruction
        assert "### Skill: decomposer-skill" in instruction
        assert "任务分解专家" in instruction
        assert "## Instruction" in instruction
        assert "请分解任务" in instruction


class TestSubTaskCreatorSkillInjection:
    """SubTaskCreator Skill 注入测试"""
    
    @pytest.fixture
    def skills_dir(self, tmp_path):
        """创建临时 Skills 目录"""
        skill_dir = tmp_path / "code-generator"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: code-generator
description: 代码生成 Skill
---

# Code Generator

你是一个代码生成专家。
""", encoding='utf-8')
        return str(tmp_path)
    
    @patch('app.core.sub_task_creator.settings')
    def test_build_description_with_skills(self, mock_settings, skills_dir):
        """测试：SubTaskCreator 构建 description 时注入 Skills"""
        from app.core.sub_task_creator import SubTaskCreator
        
        mock_settings.SKILLS_DIR = skills_dir
        mock_settings.DEFAULT_ROLE_SKILL_MAP = {
            "backend-dev": ["code-generator"]
        }
        
        creator = SubTaskCreator()
        sub_task = {
            "role": "backend-dev",
            "required_skills": ["code-generator"],
            "instruction": "生成用户模型代码",
            "output_format": "python"
        }
        
        description = creator._build_description(sub_task)
        
        assert "## Active Skills" in description
        assert "### Skill: code-generator" in description
        assert "代码生成专家" in description
        assert "## Instruction" in description
        assert "生成用户模型代码" in description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
