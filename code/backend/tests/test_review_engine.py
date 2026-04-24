"""
ReviewEngine 单元测试

测试评审引擎的核心功能：
1. 解析验收标准
2. 创建评审任务
3. 处理评审驳回
"""
import pytest
from app.core.review_engine import ReviewEngine


class TestReviewEngine:
    """ReviewEngine 测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.engine = ReviewEngine()
    
    # --- 解析验收标准测试 ---
    
    def test_parse_acceptance_criteria_empty(self):
        """测试空验收标准"""
        result = self.engine._parse_acceptance_criteria("")
        assert result == []
    
    def test_parse_acceptance_criteria_single(self):
        """测试单个验收标准"""
        result = self.engine._parse_acceptance_criteria("输出 ER 图")
        assert result == ["输出 ER 图"]
    
    def test_parse_acceptance_criteria_multiple(self):
        """测试多个验收标准"""
        acceptance = "- 输出 ER 图\n- 输出 DDL 脚本\n- 通过评审"
        result = self.engine._parse_acceptance_criteria(acceptance)
        
        assert len(result) == 3
        assert "输出 ER 图" in result
        assert "输出 DDL 脚本" in result
        assert "通过评审" in result
    
    def test_parse_acceptance_criteria_with_dashes(self):
        """测试带破折号的验收标准"""
        acceptance = """- 输出 ER 图
- 输出 DDL 脚本"""
        result = self.engine._parse_acceptance_criteria(acceptance)
        
        assert len(result) == 2
        assert result[0] == "输出 ER 图"
        assert result[1] == "输出 DDL 脚本"