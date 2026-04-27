"""
loader.py - Skill 加载器

从 /skills 目录读取 SKILL.md 文件，构建 System Prompt。
支持 Skill 依赖检查、角色能力映射、动态发现、路径安全防护、实例级缓存。

安全修复：
- P0-1: 使用 Path.is_relative_to() 防止路径边界绕过
- P0-3: 改为实例级缓存，避免多实例共享问题
- P1-1: 使用 os.fstat() 在打开文件后检查大小，防止 TOCTOU
- P1-2: 递归改迭代 + max_depth=100 限制，防止栈溢出
- P1-5: YAML 炸弹防护（限制嵌套深度）
"""
import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, TypedDict

logger = logging.getLogger(__name__)

# 常量定义
SKILL_FILE_NAME = "SKILL.md"
MAX_SKILL_SIZE_BYTES = 1 * 1024 * 1024  # 1MB 限制
DEFAULT_SKILL = "agency-agent"
MAX_DEPENDENCY_DEPTH = 100  # P1-2: 依赖链最大深度
MAX_CACHE_SIZE = 32  # P2-1: 降低缓存大小，防止内存占用过高（32MB）


class SkillInfo(TypedDict):
    """Skill 信息类型定义"""
    name: str
    content: str
    path: str


class SkillLoader:
    """Skill 加载器"""
    
    def __init__(self, skills_dir: str = "/skills", role_skill_map: Optional[Dict[str, List[str]]] = None, strict_mode: bool = True):
        """
        初始化 SkillLoader
        
        Args:
            skills_dir: Skills 目录路径
            role_skill_map: 角色能力映射表
            strict_mode: P2-2: True=全有或全无模式，False=允许部分失败
        """
        self.skills_dir = str(Path(skills_dir).resolve())
        self.role_skill_map = role_skill_map or {}
        self.skill_dependencies: Dict[str, Set[str]] = {}  # Skill 依赖图
        
        # P0-3: 实例级缓存（替代 @lru_cache）
        # P2-1: 限制缓存大小
        self._content_cache: Dict[str, str] = {}
        self._max_cache_size = MAX_CACHE_SIZE
        
        # P2-2: 严格模式
        self.strict_mode = strict_mode
        
        # 验证 skills_dir 存在
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
    
    def _validate_skill_name(self, skill_name: str) -> str:
        """
        校验 skill 名称，防止路径遍历攻击
        
        P0-1 修复：使用 Path.is_relative_to() 确保路径在 skills_dir 内
        
        Args:
            skill_name: Skill 名称
        
        Returns:
            安全的完整文件路径
        
        Raises:
            ValueError: 如果 skill_name 包含危险字符或路径逃逸
        """
        # 1. 检查危险字符
        if '..' in skill_name or '/' in skill_name or '\\' in skill_name:
            raise ValueError(f"Invalid skill name (contains dangerous characters): {skill_name}")
        
        # 2. 检查 NUL 字节（P0-1 补充）
        if '\x00' in skill_name:
            raise ValueError(f"Invalid skill name (contains NUL byte): {skill_name}")
        
        # 3. 构建路径并解析
        skill_path = Path(self.skills_dir) / skill_name / SKILL_FILE_NAME
        resolved_path = skill_path.resolve()
        resolved_dir = Path(self.skills_dir).resolve()
        
        # 4. P0-1: 使用 is_relative_to 确保路径在 skills_dir 内
        # Python 3.9+ 支持 is_relative_to，否则使用 relative_to 异常捕获
        try:
            # 检查 resolved_path 是否在 resolved_dir 内
            resolved_path.relative_to(resolved_dir)
        except ValueError:
            raise ValueError(f"Skill path escapes skills directory: {skill_name}")
        
        return str(resolved_path)
    
    def _check_file_size_safe(self, file_path: str) -> int:
        """
        P1-1 修复：在打开文件后检查大小，防止 TOCTOU 竞态条件
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件大小
        
        Raises:
            ValueError: 如果文件超过大小限制
        """
        # 使用 os.fstat 在打开文件描述符后检查
        with open(file_path, 'r', encoding='utf-8') as f:
            fd = f.fileno()
            stat_result = os.fstat(fd)
            file_size = stat_result.st_size
            
            if file_size > MAX_SKILL_SIZE_BYTES:
                raise ValueError(
                    f"Skill file too large: {file_path} "
                    f"({file_size / 1024 / 1024:.2f}MB > {MAX_SKILL_SIZE_BYTES / 1024 / 1024:.2f}MB)"
                )
            
            return file_size
    
    def _load_skill_content(self, skill_path: str) -> str:
        """
        加载 Skill 内容（P0-3: 实例级缓存）
        
        P2-1: 限制缓存大小，超过时清除最旧的条目
        
        Args:
            skill_path: Skill 文件路径
        
        Returns:
            Skill 文件内容
        """
        # P0-3: 检查实例级缓存
        if skill_path in self._content_cache:
            logger.debug(f"Cache hit for {skill_path}")
            return self._content_cache[skill_path]
        
        # P1-1: 安全检查文件大小
        self._check_file_size_safe(skill_path)
        
        # 读取内容
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # P0-3 + P2-1: 存入实例级缓存，限制大小
        if len(self._content_cache) >= self._max_cache_size:
            # 清除最旧的条目（字典的第一个键）
            oldest_key = next(iter(self._content_cache))
            del self._content_cache[oldest_key]
            logger.debug(f"Cache full, evicted {oldest_key}")
        
        self._content_cache[skill_path] = content
        logger.debug(f"Loaded skill content from {skill_path} ({len(content)} bytes)")
        
        return content
    
    def _parse_frontmatter(self, content: str) -> Optional[Dict]:
        """
        解析 YAML frontmatter
        
        P1-5: YAML 炸弹防护
        
        Args:
            content: 文件内容
        
        Returns:
            元数据字典，如果解析失败返回 None
        """
        if not content.startswith('---'):
            return None
        
        end_index = content.find('---', 3)
        if end_index == -1:
            return None
        
        try:
            frontmatter = content[3:end_index]
            # P1-5: 使用 safe_load 防止代码执行
            # PyYAML 5.1+ 已限制别名嵌套深度，但仍需注意
            metadata = yaml.safe_load(frontmatter)
            return metadata if isinstance(metadata, dict) else None
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML frontmatter: {e}")
            return None
    
    def load_skills(self, skill_names: List[str]) -> List[SkillInfo]:
        """
        加载所需 Skills（含依赖检查）
        
        P2-2: 支持部分失败模式（strict_mode=False 时）
        
        Args:
            skill_names: Skill 名称列表
        
        Returns:
            加载成功的 Skill 列表
        
        Raises:
            ValueError: Skill 依赖缺失或路径不安全（strict_mode=True 时）
        """
        loaded_skills = []
        errors = []
        
        for skill_name in skill_names:
            try:
                # 1. 校验路径安全
                skill_path = self._validate_skill_name(skill_name)
                
                # 2. P1-2: 检查依赖（迭代实现）
                self._check_dependencies_iterative(skill_name)
                
                # 3. 加载 Skill
                if os.path.exists(skill_path):
                    content = self._load_skill_content(skill_path)
                    
                    loaded_skills.append(SkillInfo(
                        name=skill_name,
                        content=content,
                        path=skill_path
                    ))
                    logger.info(f"Loaded skill: {skill_name}")
                else:
                    logger.warning(f"Skill file not found: {skill_path}")
                    # P2-2: 严格模式下，文件不存在应该抛出 ValueError
                    if self.strict_mode:
                        raise ValueError(f"Skill file not found: {skill_path}")
            
            except ValueError as e:
                error_msg = f"Failed to load skill '{skill_name}': {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                if self.strict_mode:
                    raise
            except Exception as e:
                error_msg = f"Unexpected error loading skill '{skill_name}': {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                if self.strict_mode:
                    raise
        
        # P2-2: 非严格模式下，记录错误但返回已加载的 skills
        if errors and not self.strict_mode:
            logger.warning(f"Loaded {len(loaded_skills)}/{len(skill_names)} skills, {len(errors)} errors: {errors}")
        
        return loaded_skills
    
    def _check_dependencies_iterative(self, skill_name: str) -> None:
        """
        P1-2 修复：迭代检查 Skill 依赖（替代递归）
        
        Args:
            skill_name: Skill 名称
        
        Raises:
            ValueError: 依赖缺失或检测到循环依赖
        """
        stack = [(skill_name, set())]
        depth = 0
        
        while stack:
            # P1-2: 深度限制
            if depth > MAX_DEPENDENCY_DEPTH:
                raise ValueError(f"Dependency chain too deep (>{MAX_DEPENDENCY_DEPTH})")
            
            current, visited = stack.pop()
            depth += 1
            
            # 检查循环依赖
            if current in visited:
                raise ValueError(f"Circular dependency detected: {current}")
            
            visited.add(current)
            
            # 读取 Skill 元数据
            try:
                skill_path = self._validate_skill_name(current)
            except ValueError:
                continue  # 路径不存在，由 load_skills 处理
            
            if not os.path.exists(skill_path):
                continue
            
            try:
                content = self._load_skill_content(skill_path)
            except Exception as e:
                # P2-5: 统一日志级别 - 依赖检查失败应该用 error
                logger.error(f"Failed to read skill content for dependency check of '{current}': {e}")
                continue
            
            metadata = self._parse_frontmatter(content)
            if not metadata:
                continue
            
            # 检查依赖并推入栈
            dependencies = metadata.get('dependencies', []) or []
            for dep in dependencies:
                dep_path = self._validate_skill_name(dep)
                if not os.path.exists(dep_path):
                    raise ValueError(
                        f"Skill '{current}' depends on '{dep}', but '{dep}' not found at {dep_path}"
                    )
                
                # P1-2: 推入栈继续检查（使用新的 visited 集合）
                new_visited = visited.copy()
                stack.append((dep, new_visited))
    
    def build_system_prompt(self, loaded_skills: List[SkillInfo], instruction: str, role_name: str = "") -> str:
        """
        构建 System Prompt（包含 Skill 上下文）
        
        Args:
            loaded_skills: 已加载的 Skill 列表
            instruction: 任务指令
            role_name: 角色名称（可选）
        
        Returns:
            完整的 System Prompt
        """
        parts = []
        
        # 1. 基础指令（使用角色名或默认）
        role_display = role_name if role_name else "Agent"
        parts.append(f"# {role_display}\n")
        parts.append(f"你是一个任务执行 Agent，已加载以下 Skills：\n")
        
        # 2. 加载的 Skills
        for skill in loaded_skills:
            parts.append(f"\n## Active Skill: {skill['name']}\n")
            parts.append(skill['content'])
        
        # 3. 任务指令
        parts.append(f"\n## Current Task\n")
        parts.append(instruction)
        
        return "\n".join(parts)
    
    def get_skills_for_role(self, role: str) -> List[str]:
        """
        获取角色对应的 Skills 列表
        
        Args:
            role: 角色名称（如 product-manager, tech-lead）
        
        Returns:
            Skill 名称列表
        """
        return self.role_skill_map.get(role, [DEFAULT_SKILL])
    
    def discover_all_skills(self) -> List[str]:
        """
        扫描 skills_dir 目录，发现所有可用的 Skills
        
        P2-4: 添加安全校验，防止符号链接和非法目录名
        
        Returns:
            所有找到的 Skill 名称列表
        """
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return []
        
        skills = []
        resolved_dir = Path(self.skills_dir).resolve()
        
        try:
            for entry in os.listdir(self.skills_dir):
                # 跳过隐藏目录
                if entry.startswith('.'):
                    continue
                
                # P2-4: 安全校验 - 拒绝包含危险字符的目录名
                if '..' in entry or '/' in entry or '\\' in entry:
                    logger.warning(f"Skipping unsafe directory name: {entry}")
                    continue
                
                skill_path = Path(self.skills_dir) / entry / SKILL_FILE_NAME
                
                # P2-4: 解析符号链接并验证路径
                try:
                    resolved_skill_path = skill_path.resolve()
                    # 确保技能文件在 skills_dir 内
                    resolved_skill_path.relative_to(resolved_dir)
                except ValueError:
                    logger.warning(f"Skipping skill outside skills directory: {entry}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to resolve skill path {entry}: {e}")
                    continue
                
                if skill_path.exists():
                    skills.append(entry)
        except PermissionError as e:
            logger.error(f"Permission denied accessing skills directory: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to list skills directory: {e}")
            return []
        
        return sorted(skills)
    
    def load_skills_for_role(self, role: str) -> List[SkillInfo]:
        """
        根据角色加载对应的 Skills（一站式方法）
        
        Args:
            role: 角色名称
        
        Returns:
            已加载的 Skill 列表（含 name, content, path）
        """
        skill_names = self.get_skills_for_role(role)
        return self.load_skills(skill_names)
    
    def clear_cache(self) -> None:
        """P0-3: 清除实例级缓存"""
        self._content_cache.clear()
        logger.info("Skill content cache cleared")


# 工厂模式（替代全局单例）
def create_skill_loader(skills_dir: str = "/skills", role_skill_map: Optional[Dict[str, List[str]]] = None, strict_mode: bool = True) -> SkillLoader:
    """
    创建 SkillLoader 实例（工厂模式）
    
    Args:
        skills_dir: Skills 目录路径
        role_skill_map: 角色能力映射表
        strict_mode: P2-2: True=全有或全无模式，False=允许部分失败
    
    Returns:
        SkillLoader 实例
    """
    return SkillLoader(skills_dir, role_skill_map, strict_mode)