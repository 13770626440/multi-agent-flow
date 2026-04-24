"""
parser.py - description 解析器

从 OpenMOSS 下发的 description 中提取元数据（Required Skills、Instruction、Output Format）。
"""
import re
from typing import Dict


def parse_description(description: str) -> Dict:
    """
    解析 description 中的元数据
    
    Args:
        description: OpenMOSS 下发的任务描述（Markdown 格式）
    
    Returns:
        {
            'required_skills': ['decomposer-skill', 'json-validator'],
            'instruction': '请根据需求文档分解任务...',
            'output_format': 'json'
        }
    """
    result = {
        'required_skills': [],
        'instruction': '',
        'output_format': 'text'
    }
    
    # 1. 提取 Required Skills
    skills_match = re.search(r'## Required Skills\n(.*?)(?=##|$)', description, re.DOTALL)
    if skills_match:
        skills_text = skills_match.group(1).strip()
        result['required_skills'] = [
            line.strip('- ').strip()
            for line in skills_text.split('\n')
            if line.strip()
        ]
    
    # 2. 提取 Instruction
    instruction_match = re.search(r'## Instruction\n(.*?)(?=##|$)', description, re.DOTALL)
    if instruction_match:
        result['instruction'] = instruction_match.group(1).strip()
    else:
        result['instruction'] = description
    
    # 3. 提取 Output Format
    format_match = re.search(r'## Output Format\n(.*?)(?=##|$)', description, re.DOTALL)
    if format_match:
        result['output_format'] = format_match.group(1).strip()
    
    return result
