"""
loader.py - Skill 加载器

从 /skills 目录读取 SKILL.md 文件，构建 System Prompt。
支持 Skill 依赖检查。
"""
import os
import yaml
from typing import List, Dict, Set


class SkillLoader:
    """Skill 加载器"""
    
    def __init__(self, skills_dir: str = "/skills"):
        self.skills_dir = skills_dir
        self.skill_dependencies: Dict[str, Set[str]] = {}  # Skill 依赖图
    
    def load_skills(self, skill_names: List[str]) -> List[Dict]:
        """
        加载所需 Skills（含依赖检查）
        
        Args:
            skill_names: Skill 名称列表
        
        Returns:
            加载成功的 Skill 列表
        
        Raises:
            ValueError: Skill 依赖缺失
        """
        loaded_skills = []
        
        for skill_name in skill_names:
            # 1. 检查依赖
            self._check_dependencies(skill_name)
            
            # 2. 加载 Skill
            skill_path = os.path.join(self.skills_dir, skill_name, "SKILL.md")
            
            if os.path.exists(skill_path):
                with open(skill_path, 'r', encoding='utf-8') as f:
                    skill_content = f.read()
                
                loaded_skills.append({
                    'name': skill_name,
                    'content': skill_content,
                    'path': skill_path
                })
            else:
                print(f"Warning: Skill {skill_name} not found at {skill_path}")
        
        return loaded_skills
    
    def _check_dependencies(self, skill_name: str):
        """
        检查 Skill 依赖
        
        Args:
            skill_name: Skill 名称
        
        Raises:
            ValueError: 依赖缺失
        """
        # 读取 Skill 元数据
        skill_path = os.path.join(self.skills_dir, skill_name, "SKILL.md")
        if not os.path.exists(skill_path):
            return  # 跳过不存在的 Skill（由 load_skills 处理）
        
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 YAML frontmatter
        if content.startswith('---'):
            end_index = content.find('---', 3)
            if end_index != -1:
                frontmatter = content[3:end_index]
                metadata = yaml.safe_load(frontmatter)
                
                # 检查依赖
                dependencies = metadata.get('dependencies', [])
                for dep in dependencies:
                    dep_path = os.path.join(self.skills_dir, dep, "SKILL.md")
                    if not os.path.exists(dep_path):
                        raise ValueError(
                            f"Skill '{skill_name}' depends on '{dep}', but '{dep}' not found"
                        )
    
    def build_system_prompt(self, loaded_skills: List[Dict], instruction: str) -> str:
        """
        构建 System Prompt（包含 Skill 上下文）
        
        Args:
            loaded_skills: 已加载的 Skill 列表
            instruction: 任务指令
        
        Returns:
            完整的 System Prompt
        """
        parts = []
        
        # 1. Agency Agent 基础指令
        parts.append("# Agency Agent\n")
        parts.append("你是一个任务执行 Agent，已加载以下 Skills：\n")
        
        # 2. 加载的 Skills
        for skill in loaded_skills:
            parts.append(f"\n## Active Skill: {skill['name']}\n")
            parts.append(skill['content'])
        
        # 3. 任务指令
        parts.append(f"\n## Current Task\n")
        parts.append(instruction)
        
        return "\n".join(parts)
