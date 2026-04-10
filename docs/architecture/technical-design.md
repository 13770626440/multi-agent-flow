# 技术设计文档

## 文档信息
- **文档编号**：TDD-001
- **版本**：v1.0
- **创建日期**：2026 年 4 月 9 日
- **状态**：草案，待评审
- **作者**：AI Assistant
- **审批人**：[待确认]

---

## 1. 系统架构设计

### 1.1 整体架构
```
┌─────────────────────────────────────────────────────┐
│                    用户层                            │
│  - Web Dashboard (Vue 3 + TypeScript)               │
│  - API Client (CLI/SDK)                             │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              自研·规划层（大脑）                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  Template Engine (模板引擎)                 │    │
│  │  - YAML Parser                              │    │
│  │  - Template Matcher (Embedding)             │    │
│  │  - Task Instantiator                        │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Agency-Agent Manager                       │    │
│  │  - Agency Definition                        │    │
│  │  - Agent Profile                            │    │
│  │  - Intelligent Matching                     │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Review & Optimization Engine               │    │
│  │  - Metrics Collector                        │    │
│  │  - Analysis Engine                          │    │
│  │  - Template Optimizer                       │    │
│  │  - Skill Repository                         │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                        │ REST API
                        ▼
┌─────────────────────────────────────────────────────┐
│              OpenMOSS（中枢）                        │
│  ┌─────────────────────────────────────────────┐    │
│  │  Task State Machine                         │    │
│  │  - pending → assigned → in_progress         │    │
│  │  - review → rework/done                     │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Agent Scheduler                            │    │
│  │  - Agent Pool Management                    │    │
│  │  - Task Assignment                          │    │
│  │  - Load Balancing                           │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Review & Bug System                        │    │
│  │  - Review Workflow                          │    │
│  │  - Bug Tracking                             │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Dashboard (Vue 3 + shadcn-vue)             │    │
│  │  - Task Board                               │    │
│  │  - Agent Status                             │    │
│  │  - Activity Stream                          │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                        │ cron + REST API
                        ▼
┌─────────────────────────────────────────────────────┐
│           OpenClaw Lobster（手脚）                   │
│  ┌─────────────────────────────────────────────┐    │
│  │  Agent Lifecycle                            │    │
│  │  - sessions_spawn                           │    │
│  │  - sessions_send                            │    │
│  │  - sessions_close                           │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Parallel Execution                         │    │
│  │  - parallel/barrier                         │    │
│  │  - context sharing                          │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Tool Invocation                            │    │
│  │  - Code Editor                              │    │
│  │  - File System                              │    │
│  │  - Shell Commands                           │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 1.2 技术栈
| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **后端** | Python | 3.11+ | 主要编程语言 |
| | FastAPI | 0.109+ | Web 框架 |
| | PostgreSQL | 15+ | 主数据库 |
| | Redis | 7+ | 缓存 |
| | Qdrant | 1.7+ | 向量数据库 |
| **前端** | Vue | 3.4+ | 前端框架 |
| | TypeScript | 5.3+ | 类型系统 |
| | Element Plus | 2.5+ | UI 组件库 |
| | ECharts | 5.4+ | 图表库 |
| **第三方** | OpenMOSS | v1.1.3+ | 任务调度 |
| | OpenClaw | 2026.4.5+ | Agent 执行 |

### 1.3 部署架构
```
┌─────────────────────────────────────────┐
│         Docker Compose                   │
│  ┌─────────────────────────────────┐    │
│  │  multi-agent-flow-backend       │    │
│  │  - FastAPI Server (:8000)       │    │
│  │  - Template Engine              │    │
│  │  - Agency-Agent Manager         │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  multi-agent-flow-frontend      │    │
│  │  - Nginx (:80)                  │    │
│  │  - Vue 3 App                    │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  postgresql                     │    │
│  │  - Database (:5432)             │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  redis                          │    │
│  │  - Cache (:6379)                │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  qdrant                         │    │
│  │  - Vector DB (:6333)            │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  openmoss                       │    │
│  │  - FastAPI (:6565)              │    │
│  │  - Dashboard                    │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## 2. 模块设计

### 2.1 模板引擎模块

#### 2.1.1 类设计
```python
class TemplateEngine:
    """模板引擎"""
    
    def parse_yaml(self, yaml_content: str) -> Template:
        """解析 YAML 模板"""
        pass
    
    def match_template(self, user_request: str, 
                       templates: List[Template]) -> List[TemplateMatch]:
        """匹配模板"""
        pass
    
    def instantiate(self, template: Template, 
                    variables: Dict[str, Any]) -> TaskDAG:
        """实例化模板"""
        pass
    
    def validate(self, template: Template) -> ValidationResult:
        """验证模板"""
        pass


class Template:
    """模板定义"""
    id: str
    name: str
    version: str
    phases: List[Phase]
    required_agents: Dict[str, int]
    estimated_duration: str


class Phase:
    """阶段定义"""
    name: str
    type: str  # serial | parallel
    agent_roles: List[str]
    tasks: List[Task]
    barrier: Optional[str]


class Task:
    """任务定义"""
    name: str
    agent_role: str
    description: str
    dependencies: List[str]
    expected_output: str
    review_required: bool
    review_criteria: List[str]
```

#### 2.1.2 模板匹配算法
```python
def match_template(user_request: str, templates: List[Template]) -> List[TemplateMatch]:
    """
    模板匹配算法
    
    1. 提取用户需求的关键词和语义向量
    2. 计算与每个模板的相似度
    3. 综合评分并排序
    """
    # 1. 语义相似度（70% 权重）
    user_embedding = embed(user_request)
    semantic_scores = []
    for template in templates:
        template_embedding = embed(template.description)
        semantic_score = cosine_similarity(user_embedding, template_embedding)
        semantic_scores.append(semantic_score)
    
    # 2. 关键词匹配（30% 权重）
    user_keywords = extract_keywords(user_request)
    keyword_scores = []
    for template in templates:
        template_keywords = set(template.tags)
        keyword_score = len(user_keywords & template_keywords) / len(user_keywords)
        keyword_scores.append(keyword_score)
    
    # 3. 综合评分
    final_scores = []
    for i, template in enumerate(templates):
        final_score = 0.7 * semantic_scores[i] + 0.3 * keyword_scores[i]
        
        # 4. 历史成功率加成
        historical_success_rate = template.get_historical_success_rate()
        final_score *= (0.9 + 0.1 * historical_success_rate)
        
        final_scores.append((template, final_score))
    
    # 5. 返回 Top-N
    sorted_results = sorted(final_scores, key=lambda x: x[1], reverse=True)
    return sorted_results[:5]
```

### 2.2 Agency-Agent 模块

#### 2.2.1 类设计
```python
class AgencyManager:
    """Agency 管理器"""
    
    def define_agency(self, agency_spec: Agency) -> None:
        """定义新的 Agency"""
        pass
    
    def get_agency(self, agency_name: str) -> Agency:
        """获取 Agency 定义"""
        pass
    
    def list_agencies(self) -> List[Agency]:
        """列出所有 Agency"""
        pass


class AgentManager:
    """Agent 实例管理器"""
    
    def create_agent(self, agency: Agency, 
                     project_id: str) -> Agent:
        """创建 Agent 实例"""
        pass
    
    def get_agent(self, agent_id: str) -> Agent:
        """获取 Agent 实例"""
        pass
    
    def assign_to_task(self, agent_id: str, task_id: str) -> None:
        """分配 Agent 到任务"""
        pass
    
    def track_performance(self, agent_id: str, 
                         metrics: AgentMetrics) -> None:
        """追踪 Agent 表现"""
        pass


class Agency:
    """Agency 定义（角色类型）"""
    id: str
    name: str
    description: str
    responsibilities: List[str]
    required_skills: List[str]
    career_path: List[str]
    performance_metrics: List[str]
    promotion_criteria: Dict[str, str]


class Agent:
    """Agent 实例（具体个体）"""
    id: str
    agency: str  # Agency ID
    name: str
    level: str  # Junior | Middle | Senior | Expert
    skill_mastery: Dict[str, SkillMastery]
    experience_points: int
    project_history: List[ProjectRecord]
    performance_metrics: Dict[str, float]


class SkillMastery:
    """技能掌握度"""
    skill_name: str
    level: int  # 1-10
    experience: int
    last_used: datetime
```

#### 2.2.2 智能匹配算法
```python
def match_agent_to_task(task: Task, available_agents: List[Agent]) -> Tuple[Agent, float]:
    """
    智能匹配 Agent 到任务
    
    考虑因素：
    1. 技能匹配度
    2. 经验等级
    3. 历史表现
    4. 当前负载
    """
    best_agent = None
    best_score = 0.0
    
    for agent in available_agents:
        # 1. 技能匹配度（40%）
        required_skills = task.required_skills
        skill_match_score = calculate_skill_match(agent.skill_mastery, required_skills)
        
        # 2. 经验等级（20%）
        level_score = get_level_score(agent.level)
        
        # 3. 历史表现（20%）
        performance_score = agent.performance_metrics.get('avg_score', 0.5)
        
        # 4. 当前负载（20%）
        workload_score = 1.0 - (agent.current_tasks / agent.max_tasks)
        
        # 综合评分
        final_score = (
            0.4 * skill_match_score +
            0.2 * level_score +
            0.2 * performance_score +
            0.2 * workload_score
        )
        
        if final_score > best_score:
            best_score = final_score
            best_agent = agent
    
    return best_agent, best_score
```

### 2.3 复盘优化模块

#### 2.3.1 类设计
```python
class ReviewEngine:
    """复盘引擎"""
    
    def collect_metrics(self, project_id: str) -> ProjectMetrics:
        """收集项目 metrics"""
        pass
    
    def analyze(self, metrics: ProjectMetrics) -> AnalysisResult:
        """分析数据"""
        pass
    
    def generate_recommendations(self, analysis: AnalysisResult) -> List[Recommendation]:
        """生成优化建议"""
        pass
    
    def create_optimization_draft(self, 
                                  template: Template, 
                                  recommendations: List[Recommendation]) -> Template:
        """创建优化草案"""
        pass


class SkillRepository:
    """Skill 知识库"""
    
    def add_skill(self, skill: Skill) -> None:
        """添加 Skill"""
        pass
    
    def get_skill(self, skill_id: str) -> Skill:
        """获取 Skill"""
        pass
    
    def match_skills(self, context: str) -> List[Skill]:
        """匹配相关 Skill"""
        pass
    
    def evaluate_skill(self, skill_id: str) -> SkillEvaluation:
        """评估 Skill 效果"""
        pass
```

### 2.4 OpenMOSS 集成模块

#### 2.4.1 API 客户端设计
```python
class OpenMOSSClient:
    """OpenMOSS REST API 客户端"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers['X-Agent-Key'] = api_key
    
    # 任务管理
    def create_task(self, task_spec: Dict) -> str:
        """创建任务"""
        response = self.session.post(
            f"{self.base_url}/api/tasks",
            json=task_spec
        )
        return response.json()['task_id']
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        response = self.session.get(
            f"{self.base_url}/api/tasks/{task_id}"
        )
        return TaskStatus(**response.json())
    
    # Agent 管理
    def get_agents(self) -> List[AgentInfo]:
        """获取 Agent 列表"""
        response = self.session.get(
            f"{self.base_url}/api/agents"
        )
        return [AgentInfo(**a) for a in response.json()]
    
    # 评审管理
    def submit_review(self, review_spec: Dict) -> str:
        """提交评审"""
        response = self.session.post(
            f"{self.base_url}/api/reviews",
            json=review_spec
        )
        return response.json()['review_id']
```

---

## 3. 数据库设计

### 3.1 核心表结构

#### 3.1.1 templates 表
```sql
CREATE TABLE templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    yaml_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    success_rate DECIMAL(5,2),
    usage_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE (name, version)
);
```

#### 3.1.2 projects 表
```sql
CREATE TABLE projects (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    template_id VARCHAR(50) REFERENCES templates(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    expected_duration INTERVAL,
    actual_duration INTERVAL,
    success_score DECIMAL(5,2),
    metadata JSONB
);
```

#### 3.1.3 agencies 表
```sql
CREATE TABLE agencies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    responsibilities JSONB,
    required_skills JSONB,
    career_path JSONB,
    performance_metrics JSONB,
    promotion_criteria JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.4 agents 表
```sql
CREATE TABLE agents (
    id VARCHAR(50) PRIMARY KEY,
    agency_id VARCHAR(50) REFERENCES agencies(id),
    name VARCHAR(100) NOT NULL,
    level VARCHAR(20) DEFAULT 'Junior',
    experience_points INTEGER DEFAULT 0,
    skill_mastery JSONB,
    project_history JSONB,
    performance_metrics JSONB,
    status VARCHAR(20) DEFAULT 'idle',
    current_project_id VARCHAR(50) REFERENCES projects(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.5 skills 表
```sql
CREATE TABLE skills (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    content JSONB NOT NULL,
    source_project_id VARCHAR(50) REFERENCES projects(id),
    usage_count INTEGER DEFAULT 0,
    effectiveness_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.6 project_metrics 表
```sql
CREATE TABLE project_metrics (
    id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50) REFERENCES projects(id),
    phase_name VARCHAR(100),
    duration INTERVAL,
    review_score DECIMAL(5,2),
    rework_count INTEGER,
    bug_count INTEGER,
    test_coverage DECIMAL(5,2),
    agent_performance JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. API 设计

### 4.1 核心 API

#### 4.1.1 模板管理 API
```yaml
# 创建模板
POST /api/templates
Request:
  {
    "name": "fullstack-project-dev",
    "version": "1.0",
    "description": "全栈项目开发",
    "yaml_content": "..."
  }
Response:
  {
    "template_id": "tmpl-001",
    "status": "created"
  }

# 获取模板列表
GET /api/templates?keyword=xxx&page=1&size=20
Response:
  {
    "templates": [...],
    "total": 100,
    "page": 1,
    "size": 20
  }

# 匹配模板
POST /api/templates/match
Request:
  {
    "user_request": "我需要一个用户管理系统",
    "top_n": 5
  }
Response:
  {
    "matches": [
      {
        "template_id": "tmpl-001",
        "score": 0.92,
        "name": "全栈项目开发"
      }
    ]
  }
```

#### 4.1.2 项目管理 API
```yaml
# 创建项目
POST /api/projects
Request:
  {
    "name": "用户管理系统",
    "template_id": "tmpl-001",
    "variables": {...}
  }
Response:
  {
    "project_id": "proj-001",
    "status": "created"
  }

# 获取项目状态
GET /api/projects/{project_id}
Response:
  {
    "project_id": "proj-001",
    "name": "用户管理系统",
    "status": "in_progress",
    "progress": 65,
    "phases": [...],
    "agents": [...]
  }
```

#### 4.1.3 Agent 管理 API
```yaml
# 获取 Agent 列表
GET /api/agents?agency=frontend-developer&status=idle
Response:
  {
    "agents": [
      {
        "agent_id": "agent-001",
        "agency": "frontend-developer",
        "level": "Middle",
        "status": "idle",
        "skill_mastery": {...}
      }
    ]
  }

# 创建 Agent 实例
POST /api/agents
Request:
  {
    "agency_id": "agency-frontend",
    "name": "前端开发 -A",
    "project_id": "proj-001"
  }
Response:
  {
    "agent_id": "agent-001",
    "status": "created"
  }
```

---

## 5. 阶段规划及目标

### 5.1 阶段一：基础架构搭建（2 周）
**时间**：2026-04-09 ~ 2026-04-23

#### 目标
1. ✅ 集成 OpenMOSS Dashboard
2. ✅ 实现基础 API 集成层
3. ✅ 创建简化模板系统
4. ✅ 完成"TODO 应用"端到端演示

#### 交付物
- [ ] OpenMOSS Dashboard 集成代码
- [ ] OpenMOSS REST API 客户端
- [ ] YAML 模板解析器
- [ ] 测试模板（2-3 个）
- [ ] "TODO 应用"演示

#### 技术重点
- OpenMOSS 部署和配置
- Dashboard 嵌入式集成（iframe/API）
- 基础模板匹配算法
- 任务创建和执行流程

#### 里程碑
- **M1**（4 月 15 日）：Dashboard 集成完成
- **M2**（4 月 23 日）：端到端演示完成

---

### 阶段二：核心功能完善（3 周）
**时间**：2026-04-24 ~ 2026-05-15

#### 目标
1. ✅ 完整模板系统
2. ✅ Agency-Agent 职业化体系
3. ✅ 评审和质量保证流程
4. ✅ 完成"用户管理系统"演示

#### 交付物
- [ ] 完整模板引擎（匹配、实例化）
- [ ] Agency 定义系统
- [ ] Agent 实例管理
- [ ] 智能匹配算法
- [ ] 评审系统集成
- [ ] "用户管理系统"演示

#### 技术重点
- 模板匹配优化（embedding）
- Agency-Agent 数据模型
- 智能匹配算法实现
- OpenMOSS 评审流程集成

#### 里程碑
- **M3**（5 月 1 日）：模板系统完成
- **M4**（5 月 8 日）：Agency-Agent 系统完成
- **M5**（5 月 15 日）：全栈项目演示完成

---

### 阶段三：自反馈优化系统（2 周）
**时间**：2026-05-16 ~ 2026-05-30

#### 目标
1. ✅ 自动复盘优化系统
2. ✅ Skill 知识库管理
3. ✅ 闭环优化工作流
4. ✅ 优化效果可视化

#### 交付物
- [ ] Metrics 收集系统
- [ ] 复盘分析引擎
- [ ] 优化建议生成器
- [ ] Skill 沉淀系统
- [ ] 模板优化工作流
- [ ] 优化效果追踪

#### 技术重点
- 数据收集和分析
- 根因分析算法
- Skill 提取和匹配
- 模板自动优化

#### 里程碑
- **M6**（5 月 23 日）：复盘系统完成
- **M7**（5 月 30 日）：自优化闭环完成

---

### 阶段四：Dashboard 与用户体验（1-2 周）
**时间**：2026-05-31 ~ 2026-06-13

#### 目标
1. ✅ 完整 Web Dashboard
2. ✅ 用户友好的管理界面
3. ✅ 部署包和文档
4. ✅ 演示视频和案例

#### 交付物
- [ ] 项目管理界面
- [ ] 模板管理界面
- [ ] Agency-Agent 管理界面
- [ ] 优化历史界面
- [ ] 部署文档
- [ ] 用户手册

#### 技术重点
- Dashboard 前端开发
- 与 OpenMOSS Dashboard 深度集成
- 用户体验优化
- 性能优化

#### 里程碑
- **M8**（6 月 6 日）：Dashboard 完成
- **M9**（6 月 13 日）：产品发布

---

## 6. 风险与技术挑战

### 6.1 技术风险
| 风险 | 可能性 | 影响 | 缓解策略 | 阶段 |
|------|--------|------|----------|------|
| OpenMOSS 集成复杂度高 | 中 | 高 | 1. 先用 iframe 方案<br>2. 准备备选方案<br>3. 早期验证 | 阶段一 |
| 模板匹配效果不佳 | 中 | 中 | 1. 先实现简单版本<br>2. 逐步优化算法<br>3. A/B 测试 | 阶段一 |
| Agency-Agent 数据模型复杂 | 高 | 中 | 1. 简化初始模型<br>2. 迭代完善<br>3. 参考 agency-agents | 阶段二 |
| 复盘算法准确率低 | 高 | 中 | 1. 基于规则引擎<br>2. 人工标注训练<br>3. 逐步引入 ML | 阶段三 |

### 6.2 性能挑战
| 挑战 | 目标 | 优化策略 |
|------|------|----------|
| API 响应时间 | < 500ms | 1. Redis 缓存<br>2. 数据库索引<br>3. 异步处理 |
| 模板匹配速度 | < 2 秒 | 1. 向量数据库<br>2. 预计算 embedding<br>3. 批量处理 |
| Dashboard 加载 | < 2 秒 | 1. 前端优化<br>2. 数据分页<br>3. 懒加载 |

---

## 7. 质量保证

### 7.1 代码质量
- **编码规范**：遵循 PEP 8（Python）、Vue Style Guide
- **代码审查**：所有代码必须经过至少 1 人审查
- **测试覆盖率**：单元测试覆盖率 ≥ 80%
- **文档完整性**：所有模块必须有文档字符串

### 7.2 测试策略
- **单元测试**：pytest（Python）、Jest（JavaScript）
- **集成测试**：测试 OpenMOSS/OpenClaw 集成
- **端到端测试**：完整项目流程测试
- **性能测试**：API 压力测试

### 7.3 持续集成
- **代码检查**：flake8、eslint、prettier
- **自动化测试**：GitHub Actions / GitLab CI
- **部署流程**：Docker Compose 一键部署

---

## 8. 附录

### 8.1 参考文档
- 需求文档：requirements/functional/functional-requirements.md
- 项目计划：plans/phase1/phase1-plan-draft.md
- 约束文档：docs/development/project-constraints-and-process.md

### 8.2 术语表
- **Agency**：Agent 角色类型（职业）
- **Agent**：具体的 Agent 实例
- **Template**：任务计划模板
- **Skill**：Agent 的技能和知识包
- **Dashboard**：系统管理和监控界面

### 8.3 变更记录
| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|----------|--------|
| v1.0 | 2026-04-09 | 初始版本 | AI Assistant |

---

*文档结束*
