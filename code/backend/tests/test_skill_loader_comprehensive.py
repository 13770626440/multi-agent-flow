"""
test_skill_loader_comprehensive.py - SkillLoader 综合测试

覆盖所有评审发现的问题：
- 路径遍历攻击测试
- YAML 畸形文件测试
- 依赖缺失/传递依赖测试
- 空目录/空文件测试
- 文件大小限制测试
- 缓存测试
- 并发安全测试
"""
import os
import sys
import pytest
import tempfile
import importlib.util
from typing import Dict, List

# 导入 SkillLoader
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
loader_path = os.path.join(backend_dir, "skills", "agency-agent", "loader.py")
_spec = importlib.util.spec_from_file_location("skill_loader", loader_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

SkillLoader = _module.SkillLoader
create_skill_loader = _module.create_skill_loader
SKILL_FILE_NAME = _module.SKILL_FILE_NAME
MAX_SKILL_SIZE_BYTES = _module.MAX_SKILL_SIZE_BYTES


class TestPathTraversal:
    """路径遍历攻击测试"""
    
    def test_dotdot_in_skill_name(self, tmp_path):
        """测试：skill_name 包含 .."""
        loader = create_skill_loader(str(tmp_path))
        
        with pytest.raises(ValueError, match="contains dangerous characters"):
            loader._validate_skill_name("../etc/passwd")
    
    def test_slash_in_skill_name(self, tmp_path):
        """测试：skill_name 包含 /"""
        loader = create_skill_loader(str(tmp_path))
        
        with pytest.raises(ValueError, match="contains dangerous characters"):
            loader._validate_skill_name("skill/sub")
    
    def test_backslash_in_skill_name(self, tmp_path):
        """测试：skill_name 包含 \\"""
        loader = create_skill_loader(str(tmp_path))
        
        with pytest.raises(ValueError, match="contains dangerous characters"):
            loader._validate_skill_name("skill\\sub")
    
    def test_path_escape_attempt(self, tmp_path):
        """测试：路径逃逸尝试"""
        # 创建 skills 目录
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        
        loader = create_skill_loader(str(skills_dir))
        
        # 尝试通过多个 .. 逃逸
        with pytest.raises(ValueError, match="contains dangerous characters"):
            loader._validate_skill_name("../../etc/passwd")


class TestYAMLMalformed:
    """YAML 畸形文件测试"""
    
    def test_invalid_yaml_frontmatter(self, tmp_path):
        """测试：YAML frontmatter 格式错误"""
        skill_dir = tmp_path / "bad-yaml"
        skill_dir.mkdir()
        (skill_dir / SKILL_FILE_NAME).write_text("""---
name: bad-yaml
dependencies: [invalid yaml {{{
---

# Bad YAML
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        # 应该能加载文件，但解析 frontmatter 返回 None
        skills = loader.load_skills(["bad-yaml"])
        assert len(skills) == 1  # 文件能加载
        # 依赖检查应该跳过（因为解析失败）
    
    def test_no_frontmatter(self, tmp_path):
        """测试：没有 frontmatter"""
        skill_dir = tmp_path / "no-frontmatter"
        skill_dir.mkdir()
        (skill_dir / SKILL_FILE_NAME).write_text("""# No Frontmatter

This file has no YAML frontmatter.
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        skills = loader.load_skills(["no-frontmatter"])
        assert len(skills) == 1
    
    def test_empty_file(self, tmp_path):
        """测试：空文件"""
        skill_dir = tmp_path / "empty"
        skill_dir.mkdir()
        (skill_dir / SKILL_FILE_NAME).write_text("", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        skills = loader.load_skills(["empty"])
        assert len(skills) == 1


class TestDependencyChecking:
    """依赖检查测试"""
    
    def test_missing_direct_dependency(self, tmp_path):
        """测试：直接依赖缺失"""
        # 创建 skill A 依赖 B，但 B 不存在
        skill_a_dir = tmp_path / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / SKILL_FILE_NAME).write_text("""---
name: skill-a
dependencies:
  - skill-b
---

# Skill A
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        
        with pytest.raises(ValueError, match="depends on 'skill-b'"):
            loader.load_skills(["skill-a"])
    
    def test_missing_transitive_dependency(self, tmp_path):
        """测试：传递依赖缺失（A -> B -> C，C 缺失）"""
        # Skill A 依赖 B
        skill_a_dir = tmp_path / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / SKILL_FILE_NAME).write_text("""---
name: skill-a
dependencies:
  - skill-b
---

# Skill A
""", encoding='utf-8')
        
        # Skill B 依赖 C（但 C 不存在）
        skill_b_dir = tmp_path / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / SKILL_FILE_NAME).write_text("""---
name: skill-b
dependencies:
  - skill-c
---

# Skill B
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        
        with pytest.raises(ValueError, match="depends on 'skill-c'"):
            loader.load_skills(["skill-a"])
    
    def test_circular_dependency(self, tmp_path):
        """测试：循环依赖（A -> B -> A）"""
        # Skill A 依赖 B
        skill_a_dir = tmp_path / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / SKILL_FILE_NAME).write_text("""---
name: skill-a
dependencies:
  - skill-b
---

# Skill A
""", encoding='utf-8')
        
        # Skill B 依赖 A
        skill_b_dir = tmp_path / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / SKILL_FILE_NAME).write_text("""---
name: skill-b
dependencies:
  - skill-a
---

# Skill B
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        
        with pytest.raises(ValueError, match="Circular dependency"):
            loader.load_skills(["skill-a"])
    
    def test_valid_dependencies(self, tmp_path):
        """测试：有效的依赖链"""
        # Skill C（无依赖）
        skill_c_dir = tmp_path / "skill-c"
        skill_c_dir.mkdir()
        (skill_c_dir / SKILL_FILE_NAME).write_text("""---
name: skill-c
dependencies: []
---

# Skill C
""", encoding='utf-8')
        
        # Skill B 依赖 C
        skill_b_dir = tmp_path / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / SKILL_FILE_NAME).write_text("""---
name: skill-b
dependencies:
  - skill-c
---

# Skill B
""", encoding='utf-8')
        
        # Skill A 依赖 B
        skill_a_dir = tmp_path / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / SKILL_FILE_NAME).write_text("""---
name: skill-a
dependencies:
  - skill-b
---

# Skill A
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        skills = loader.load_skills(["skill-a"])
        
        assert len(skills) == 1
        assert skills[0]["name"] == "skill-a"


class TestFileSizeLimit:
    """文件大小限制测试"""
    
    def test_oversized_file(self, tmp_path):
        """测试：文件超过大小限制"""
        skill_dir = tmp_path / "big-skill"
        skill_dir.mkdir()
        
        # 创建超过 1MB 的文件
        content = "x" * (MAX_SKILL_SIZE_BYTES + 1)
        (skill_dir / SKILL_FILE_NAME).write_text(content, encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        
        with pytest.raises(ValueError, match="too large"):
            loader.load_skills(["big-skill"])
    
    def test_valid_file_size(self, tmp_path):
        """测试：文件大小在限制内"""
        skill_dir = tmp_path / "small-skill"
        skill_dir.mkdir()
        (skill_dir / SKILL_FILE_NAME).write_text("""---
name: small-skill
---

# Small Skill
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        skills = loader.load_skills(["small-skill"])
        
        assert len(skills) == 1


class TestCaching:
    """缓存测试"""
    
    def test_cache_hits(self, tmp_path):
        """测试：缓存命中"""
        skill_dir = tmp_path / "cached-skill"
        skill_dir.mkdir()
        (skill_dir / SKILL_FILE_NAME).write_text("""---
name: cached-skill
---

# Cached Skill
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        
        # 第一次加载
        skills1 = loader.load_skills(["cached-skill"])
        assert len(skills1) == 1
        
        # 第二次加载（应该命中缓存）
        skills2 = loader.load_skills(["cached-skill"])
        assert len(skills2) == 1
        
        # 内容相同
        assert skills1[0]["content"] == skills2[0]["content"]
    
    def test_clear_cache(self, tmp_path):
        """测试：清除缓存"""
        skill_dir = tmp_path / "cache-clear"
        skill_dir.mkdir()
        (skill_dir / SKILL_FILE_NAME).write_text("""---
name: cache-clear
---

# Cache Clear
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        
        # 加载并缓存
        loader.load_skills(["cache-clear"])
        
        # 清除缓存
        loader.clear_cache()
        
        # P0-3 修复后使用实例级缓存，验证缓存已清空
        assert len(loader._content_cache) == 0


class TestEmptyDirectory:
    """空目录/不存在目录测试"""
    
    def test_nonexistent_directory(self):
        """测试：skills_dir 不存在"""
        loader = create_skill_loader("/nonexistent/path")
        
        skills = loader.discover_all_skills()
        assert skills == []
    
    def test_empty_directory(self, tmp_path):
        """测试：空目录"""
        loader = create_skill_loader(str(tmp_path))
        
        skills = loader.discover_all_skills()
        assert skills == []
    
    def test_load_nonexistent_skill(self, tmp_path):
        """测试：加载不存在的 skill"""
        # P2-2: 使用非严格模式
        loader = create_skill_loader(str(tmp_path), strict_mode=False)
        
        skills = loader.load_skills(["nonexistent"])
        assert skills == []


class TestRoleSkillMapping:
    """角色能力映射测试"""
    
    def test_default_role(self, tmp_path):
        """测试：未配置的角色返回默认 skill"""
        loader = create_skill_loader(str(tmp_path))
        
        skills = loader.get_skills_for_role("unknown-role")
        assert skills == ["agency-agent"]
    
    def test_configured_role(self, tmp_path):
        """测试：已配置的角色"""
        role_map = {
            "tech-lead": ["skill-a", "skill-b"],
            "executor": ["skill-c"]
        }
        loader = create_skill_loader(str(tmp_path), role_map)
        
        assert loader.get_skills_for_role("tech-lead") == ["skill-a", "skill-b"]
        assert loader.get_skills_for_role("executor") == ["skill-c"]


class TestBuildSystemPrompt:
    """System Prompt 构建测试"""
    
    def test_with_role_name(self, tmp_path):
        """测试：带角色名"""
        loader = create_skill_loader(str(tmp_path))
        
        skills = [{"name": "test", "content": "# Test", "path": "/test"}]
        prompt = loader.build_system_prompt(skills, "Execute task", "tech-lead")
        
        assert "# tech-lead" in prompt
        assert "## Active Skill: test" in prompt
        assert "Execute task" in prompt
    
    def test_without_role_name(self, tmp_path):
        """测试：不带角色名"""
        loader = create_skill_loader(str(tmp_path))
        
        skills = [{"name": "test", "content": "# Test", "path": "/test"}]
        prompt = loader.build_system_prompt(skills, "Execute task")
        
        assert "# Agent" in prompt
        assert "## Active Skill: test" in prompt


class TestConcurrency:
    """并发安全测试"""
    
    def test_concurrent_load(self, tmp_path):
        """测试：并发加载同一 skill"""
        import threading
        
        skill_dir = tmp_path / "concurrent"
        skill_dir.mkdir()
        (skill_dir / SKILL_FILE_NAME).write_text("""---
name: concurrent
---

# Concurrent Skill
""", encoding='utf-8')
        
        loader = create_skill_loader(str(tmp_path))
        results = []
        errors = []
        
        def load_skill():
            try:
                skills = loader.load_skills(["concurrent"])
                results.append(skills)
            except Exception as e:
                errors.append(e)
        
        # 创建 10 个线程同时加载
        threads = [threading.Thread(target=load_skill) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 所有线程都应该成功
        assert len(errors) == 0
        assert len(results) == 10
        for r in results:
            assert len(r) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
