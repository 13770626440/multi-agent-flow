"""快速验证 Skill 动态加载集成"""
import sys
import os

# 添加 backend 到路径
backend_dir = r"D:\coding\multi-agent-flow\code\backend"
sys.path.insert(0, backend_dir)

# 测试 1: SkillLoader 基础功能
print("=" * 60)
print("测试 1: SkillLoader 基础功能")
print("=" * 60)

import importlib.util
loader_spec = importlib.util.spec_from_file_location(
    "skill_loader",
    os.path.join(backend_dir, "skills", "agency-agent", "loader.py")
)
skill_loader_module = importlib.util.module_from_spec(loader_spec)
loader_spec.loader.exec_module(skill_loader_module)

SkillLoader = skill_loader_module.SkillLoader

# 创建测试 Skills 目录
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    # 创建测试 skill
    skill_dir = os.path.join(tmpdir, "test-skill")
    os.makedirs(skill_dir)
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""---
name: test-skill
description: 测试 Skill
---

# Test Skill
这是测试内容。
""")
    
    loader = SkillLoader(tmpdir, {"tech-lead": ["test-skill"]})
    
    # 测试加载
    skills = loader.load_skills_for_role("tech-lead")
    print(f"  加载 Skills: {[s['name'] for s in skills]}")
    assert len(skills) == 1
    assert skills[0]["name"] == "test-skill"
    print("  [PASS] 角色技能加载成功")
    
    # 测试发现
    all_skills = loader.discover_all_skills()
    print(f"  发现 Skills: {all_skills}")
    assert "test-skill" in all_skills
    print("  [PASS] Skill 发现成功")
    
    # 测试 System Prompt 构建
    prompt = loader.build_system_prompt(skills, "请执行任务")
    assert "## Active Skill: test-skill" in prompt
    assert "请执行任务" in prompt
    print("  [PASS] System Prompt 构建成功")

print("\n" + "=" * 60)
print("测试 2: Decomposer Skill 注入")
print("=" * 60)

from unittest.mock import patch, MagicMock

with tempfile.TemporaryDirectory() as tmpdir:
    skill_dir = os.path.join(tmpdir, "decomposer-skill")
    os.makedirs(skill_dir)
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""---
name: decomposer-skill
description: 任务分解 Skill
---

# Decomposer
你是任务分解专家。
""")
    
    mock_settings = MagicMock()
    mock_settings.SKILLS_DIR = tmpdir
    mock_settings.DEFAULT_ROLE_SKILL_MAP = {"tech-lead": ["decomposer-skill"]}
    
    # 先导入模块，再 patch
    import app.core.decomposer as decomposer_module
    original_settings = decomposer_module.settings
    
    try:
        decomposer_module.settings = mock_settings
        
        decomposer = decomposer_module.Decomposer()
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
        print("  [PASS] Decomposer Skill 注入成功")
    finally:
        decomposer_module.settings = original_settings

print("\n" + "=" * 60)
print("测试 3: SubTaskCreator Skill 注入")
print("=" * 60)

with tempfile.TemporaryDirectory() as tmpdir:
    skill_dir = os.path.join(tmpdir, "code-generator")
    os.makedirs(skill_dir)
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""---
name: code-generator
description: 代码生成 Skill
---

# Code Generator
你是代码生成专家。
""")
    
    mock_settings = MagicMock()
    mock_settings.SKILLS_DIR = tmpdir
    mock_settings.DEFAULT_ROLE_SKILL_MAP = {"backend-dev": ["code-generator"]}
    
    import app.core.sub_task_creator as stc_module
    original_settings = stc_module.settings
    
    try:
        stc_module.settings = mock_settings
        
        creator = stc_module.SubTaskCreator()
        sub_task = {
            "role": "backend-dev",
            "required_skills": ["code-generator"],
            "instruction": "生成代码",
            "output_format": "python"
        }
        
        description = creator._build_description(sub_task)
        
        assert "## Active Skills" in description
        assert "### Skill: code-generator" in description
        assert "代码生成专家" in description
        print("  [PASS] SubTaskCreator Skill 注入成功")
    finally:
        stc_module.settings = original_settings

print("\n" + "=" * 60)
print("所有测试通过！")
print("=" * 60)
print("\n结论:")
print("  [PASS] SkillLoader 能正确加载角色对应的 Skills")
print("  [PASS] SkillLoader 能发现所有可用 Skills")
print("  [PASS] SkillLoader 能构建包含 Skill 内容的 System Prompt")
print("  [PASS] Decomposer 能在指令中注入 Skills")
print("  [PASS] SubTaskCreator 能在 description 中注入 Skills")
