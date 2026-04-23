"""
DAGEngine - 基于 networkx 的 DAG 依赖引擎

负责任务依赖管理、拓扑排序、就绪任务检测。
"""
import networkx as nx
import logging
from typing import List, Set, Dict, Any

logger = logging.getLogger(__name__)


class DAGEngine:
    """DAG 依赖引擎"""
    
    def __init__(self, tasks: List[Dict[str, Any]]):
        """
        初始化 DAG 引擎
        
        Args:
            tasks: 子任务列表，每个任务包含 id 和 dependencies 字段
        """
        self.graph = nx.DiGraph()
        self.task_map = {task["id"]: task for task in tasks}
        
        for task in tasks:
            self.graph.add_node(task["id"])
            for dep_id in task.get("dependencies", []):
                self.graph.add_edge(dep_id, task["id"])
        
        # 校验是否为有效 DAG
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Circular dependency detected in tasks")
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """
        获取当前可执行的任务（所有依赖已完成）
        
        Args:
            completed_tasks: 已完成的任务 ID 集合
            
        Returns:
            可执行的任务 ID 列表
        """
        ready = []
        for task_id in self.graph.nodes():
            if task_id in completed_tasks:
                continue
            predecessors = set(self.graph.predecessors(task_id))
            if predecessors.issubset(completed_tasks):
                ready.append(task_id)
        return ready
    
    def get_execution_order(self) -> List[str]:
        """
        获取拓扑排序后的执行顺序
        
        Returns:
            按依赖顺序排列的任务 ID 列表
        """
        return list(nx.topological_sort(self.graph))
    
    def get_dependents(self, task_id: str) -> List[str]:
        """
        获取依赖指定任务的所有后续任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            后续任务 ID 列表
        """
        return list(self.graph.successors(task_id))
    
    def get_dependencies(self, task_id: str) -> List[str]:
        """
        获取指定任务的所有前置依赖
        
        Args:
            task_id: 任务 ID
            
        Returns:
            前置任务 ID 列表
        """
        return list(self.graph.predecessors(task_id))
    
    def to_dict(self) -> Dict[str, Any]:
        """将 DAG 导出为字典（用于持久化）"""
        return {
            "nodes": list(self.graph.nodes()),
            "edges": list(self.graph.edges()),
            "tasks": self.task_map
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DAGEngine":
        """从字典恢复 DAG 引擎"""
        tasks = data.get("tasks", {}).values()
        engine = cls.__new__(cls)
        engine.graph = nx.DiGraph()
        engine.graph.add_nodes_from(data.get("nodes", []))
        engine.graph.add_edges_from(data.get("edges", []))
        engine.task_map = data.get("tasks", {})
        return engine
