"""
agency-agent parser 单元测试

测试 description 解析器的核心功能：
1. 提取 Required Skills
2. 提取 Instruction
3. 提取 Output Format
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'agency-agent'))
from parser import parse_description


class TestParser:
    """parser 测试类"""
    
    def test_parse_description_full(self):
        """测试完整 description 解析"""
        description = """## Required Skills
- decomposer-skill
- json-validator

## Instruction
请根据需求文档分解任务...

## Output Format
json"""
        
        result = parse_description(description)
        
        assert result['required_skills'] == ['decomposer-skill', 'json-validator']
        assert '请根据需求文档分解任务' in result['instruction']
        assert result['output_format'] == 'json'
    
    def test_parse_description_no_skills(self):
        """测试无 Skills 的 description"""
        description = """## Instruction
请执行任务...

## Output Format
text"""
        
        result = parse_description(description)
        
        assert result['required_skills'] == []
        assert '请执行任务' in result['instruction']
        assert result['output_format'] == 'text'
    
    def test_parse_description_only_instruction(self):
        """测试仅有 Instruction"""
        description = "请执行任务..."
        
        result = parse_description(description)
        
        assert result['required_skills'] == []
        assert result['instruction'] == "请执行任务..."
        assert result['output_format'] == 'text'
    
    def test_parse_description_with_empty_lines(self):
        """测试包含空行的 description"""
        description = """## Required Skills
- skill1

- skill2

## Instruction
指令内容"""
        
        result = parse_description(description)
        
        assert result['required_skills'] == ['skill1', 'skill2']