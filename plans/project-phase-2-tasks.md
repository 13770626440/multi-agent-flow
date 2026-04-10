# 阶段二：核心功能 - 详细任务表

## 阶段信息
- **阶段名称**: 核心功能
- **工期**: 3 周（2026-05-02 至 05-22）
- **目标**: Agency-Agent 体系，评审流程，用户管理系统演示
- **总任务数**: 待分解
- **单任务时长**: ≤15 分钟

---

## 阶段二-1：完整模板系统（第 1 周，05-02 至 05-08）

### 任务 1: 创建 templates 表
**任务 ID**: TMPL-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- PostgreSQL 数据库连接
- 设计文档：technical-design.md

**执行步骤**:
1. 执行 SQL 创建 templates 表
2. 创建索引（name, version）
3. 验证表结构

**输出**:
- templates 表创建成功
- 索引创建成功

**验证方法**:
```sql
\d templates
\di templates
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS templates CASCADE;
```

**验收标准**:
- [ ] 表结构符合设计（id, name, version, yaml_content, created_at）
- [ ] 唯一索引（name, version）生效
- [ ] 可以插入测试数据

---

### 任务 2: 创建 projects 表
**任务 ID**: TMPL-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- templates 表已创建

**执行步骤**:
1. 执行 SQL 创建 projects 表
2. 创建外键约束（template_id → templates）
3. 创建索引（status, created_at）

**输出**:
- projects 表创建成功
- 外键约束生效

**验证方法**:
```sql
\d projects
SELECT conname FROM pg_constraint WHERE conname LIKE '%projects%';
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS projects CASCADE;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### 任务 3: 创建 project_metrics 表
**任务 ID**: TMPL-001-T03
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- projects 表已创建

**执行步骤**:
1. 执行 SQL 创建 project_metrics 表
2. 创建外键约束（project_id → projects）
3. 创建索引（project_id, action_time）

**输出**:
- project_metrics 表创建成功

**验证方法**:
```sql
\d project_metrics
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS project_metrics;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### 任务 4: 实现 YAML 模板解析器
**任务 ID**: TMPL-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Python 环境
- PyYAML 库

**执行步骤**:
1. 安装 PyYAML：`pip install pyyaml`
2. 创建 services/template_parser.py
3. 实现 parse_yaml 函数
4. 实现 validate_template 函数
5. 实现 LRU 缓存

**输出**:
- services/template_parser.py 文件
- parse_yaml 函数
- validate_template 函数

**验证方法**:
```python
from services.template_parser import parse_yaml
yaml_content = """
name: test-template
version: "1.0"
phases:
  - name: Phase 1
    tasks:
      - name: Task 1
"""
template = parse_yaml(yaml_content)
assert template["name"] == "test-template"
```

**回滚方案**:
```bash
rm services/template_parser.py
```

**验收标准**:
- [ ] YAML 解析正确
- [ ] 验证逻辑正确
- [ ] 缓存生效

---

### 任务 5: 实现模板验证逻辑
**任务 ID**: TMPL-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- services/template_parser.py 已创建

**执行步骤**:
1. 实现 validate_phases 函数
2. 实现 validate_tasks 函数
3. 实现 validate_dependencies 函数
4. 实现 validate_agent_roles 函数

**输出**:
- validate_phases 函数
- validate_tasks 函数
- validate_dependencies 函数
- validate_agent_roles 函数

**验证方法**:
```python
from services.template_parser import validate_template
template = {"phases": [...]}
errors = validate_template(template)
assert len(errors) == 0
```

**回滚方案**:
```bash
# 回滚到上一个版本
git checkout HEAD~1 services/template_parser.py
```

**验收标准**:
- [ ] Phase 验证正确
- [ ] Task 验证正确
- [ ] 依赖验证正确
- [ ] Agent 角色验证正确

---

### 任务 6: 实现模板存储 API
**任务 ID**: TMPL-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- FastAPI 环境
- templates 表已创建

**执行步骤**:
1. 创建 api/templates.py
2. 实现 POST /api/templates 端点
3. 实现 GET /api/templates 端点
4. 实现 GET /api/templates/{template_id} 端点

**输出**:
- api/templates.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/templates \
  -H "Content-Type: application/json" \
  -d '{"name":"test","version":"1.0","yaml_content":"..."}'
```

**回滚方案**:
```bash
rm api/templates.py
```

**验收标准**:
- [ ] 创建模板成功
- [ ] 查询列表成功
- [ ] 查询详情成功

---

### 任务 7: 实现模板更新 API
**任务 ID**: TMPL-001-T07
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- api/templates.py 已创建

**执行步骤**:
1. 实现 PUT /api/templates/{template_id} 端点
2. 实现版本检查逻辑
3. 实现版本历史记录

**输出**:
- PUT /api/templates/{template_id} 端点

**验证方法**:
```bash
curl -X PUT http://localhost:8000/api/templates/uuid \
  -H "Content-Type: application/json" \
  -d '{"version":"1.1","yaml_content":"..."}'
```

**回滚方案**:
```bash
# 注释掉 PUT 端点
```

**验收标准**:
- [ ] 更新成功
- [ ] 版本号自动递增
- [ ] 历史记录保存

---

### 任务 8: 实现模板删除 API
**任务 ID**: TMPL-001-T08
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- api/templates.py 已创建

**执行步骤**:
1. 实现 DELETE /api/templates/{template_id} 端点
2. 实现软删除逻辑（status = 'inactive'）
3. 实现级联检查

**输出**:
- DELETE /api/templates/{template_id} 端点

**验证方法**:
```bash
curl -X DELETE http://localhost:8000/api/templates/uuid
```

**回滚方案**:
```bash
# 注释掉 DELETE 端点
```

**验收标准**:
- [ ] 删除成功（软删除）
- [ ] 级联检查生效

---

### 任务 9: 实现模板匹配算法（关键词）
**任务 ID**: TMPL-001-T09
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- templates 表已创建

**执行步骤**:
1. 创建 services/template_matcher.py
2. 实现 extract_keywords 函数
3. 实现 keyword_match 函数
4. 实现 calculate_score 函数

**输出**:
- services/template_matcher.py 文件
- 3 个匹配函数

**验证方法**:
```python
from services.template_matcher import keyword_match
keywords = ["用户管理", "CRUD"]
template_tags = ["用户", "管理", "系统"]
score = keyword_match(keywords, template_tags)
assert score > 0.5
```

**回滚方案**:
```bash
rm services/template_matcher.py
```

**验收标准**:
- [ ] 关键词提取正确
- [ ] 匹配分数计算正确
- [ ] 返回 Top-N 结果

---

### 任务 10: 实现模板匹配 API
**任务 ID**: TMPL-001-T10
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- services/template_matcher.py 已创建

**执行步骤**:
1. 实现 POST /api/templates/match 端点
2. 调用 matcher 服务
3. 返回匹配结果（Top-5）

**输出**:
- POST /api/templates/match 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/templates/match \
  -H "Content-Type: application/json" \
  -d '{"user_request":"用户管理系统","top_n":5}'
```

**回滚方案**:
```bash
# 注释掉 match 端点
```

**验收标准**:
- [ ] 匹配请求成功
- [ ] 返回 Top-5 结果
- [ ] 分数排序正确

---

### 任务 11: 实现模板实例化
**任务 ID**: TMPL-001-T11
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- services/template_parser.py 已创建
- services/template_matcher.py 已创建

**执行步骤**:
1. 创建 services/template_instantiator.py
2. 实现 instantiate_template 函数
3. 实现 fill_variables 函数
4. 实现 generate_dag 函数

**输出**:
- services/template_instantiator.py 文件
- 3 个实例化函数

**验证方法**:
```python
from services.template_instantiator import instantiate_template
template = {...}
variables = {"project_name": "用户管理系统"}
dag = instantiate_template(template, variables)
assert "phases" in dag
```

**回滚方案**:
```bash
rm services/template_instantiator.py
```

**验收标准**:
- [ ] 模板实例化成功
- [ ] 变量填充正确
- [ ] DAG 生成正确

---

### 任务 12: 实现 DAG 可视化
**任务 ID**: TMPL-001-T12
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- services/template_instantiator.py 已创建

**执行步骤**:
1. 安装 networkx：`pip install networkx`
2. 安装 pyvis：`pip install pyvis`
3. 实现 build_dag 函数
4. 实现 visualize_dag 函数

**输出**:
- build_dag 函数
- visualize_dag 函数
- HTML 可视化文件

**验证方法**:
```python
from services.dag_builder import build_dag, visualize_dag
dag = build_dag(phases)
visualize_dag(dag, "output.html")
```

**回滚方案**:
```bash
rm services/dag_builder.py
```

**验收标准**:
- [ ] DAG 构建正确
- [ ] 可视化文件生成
- [ ] 依赖关系清晰

---

### 任务 13: 创建测试模板（simple-webpage）
**任务 ID**: TMPL-001-T13
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- templates 表已创建
- API 端点已创建

**执行步骤**:
1. 创建 templates/simple-webpage.yaml
2. 定义 3 个 Phase（需求、设计、开发）
3. 定义每个 Phase 的 Task
4. 通过 API 导入模板

**输出**:
- templates/simple-webpage.yaml 文件
- 模板导入成功

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/templates \
  -H "Content-Type: application/json" \
  --data-binary @templates/simple-webpage.yaml
```

**回滚方案**:
```bash
# 通过 API 删除模板
curl -X DELETE http://localhost:8000/api/templates/uuid
```

**验收标准**:
- [ ] YAML 格式正确
- [ ] Phase 定义完整
- [ ] Task 定义完整
- [ ] 导入成功

---

### 任务 14: 创建测试模板（todo-app）
**任务 ID**: TMPL-001-T14
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- templates/simple-webpage.yaml 已创建

**执行步骤**:
1. 创建 templates/todo-app.yaml
2. 定义 4 个 Phase（需求、设计、开发、测试）
3. 定义并行执行（开发 + 测试准备）
4. 通过 API 导入模板

**输出**:
- templates/todo-app.yaml 文件

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/templates ...
```

**回滚方案**:
```bash
rm templates/todo-app.yaml
```

**验收标准**:
- [ ] YAML 格式正确
- [ ] 并行执行定义正确
- [ ] 导入成功

---

### 任务 15: 编写模板单元测试
**任务 ID**: TMPL-001-T15
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有模板代码已完成

**执行步骤**:
1. 创建 tests/test_templates.py
2. 编写解析器测试
3. 编写匹配器测试
4. 编写实例化测试
5. 运行测试

**输出**:
- tests/test_templates.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_templates.py -v
```

**回滚方案**:
```bash
rm tests/test_templates.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

## 阶段二-2：Agency-Agent 系统（第 2 周，05-09 至 05-15）

### 任务 16: 创建 agencies 表
**任务 ID**: AGENT-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- PostgreSQL 数据库连接

**执行步骤**:
1. 执行 SQL 创建 agencies 表
2. 创建索引（name）
3. 插入预定义 Agency（5 个）

**输出**:
- agencies 表创建成功
- 5 个预定义 Agency 数据

**验证方法**:
```sql
SELECT * FROM agencies;
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS agencies CASCADE;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 5 个 Agency 已插入（admin, pm, developer, tester, viewer）

---

### 任务 17: 创建 agent_profiles 表
**任务 ID**: AGENT-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- agencies 表已创建
- users 表已创建

**执行步骤**:
1. 执行 SQL 创建 agent_profiles 表
2. 创建外键（agency_id, user_id）
3. 创建索引（agency_id, status）

**输出**:
- agent_profiles 表创建成功

**验证方法**:
```sql
\d agent_profiles
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS agent_profiles;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### 任务 18: 创建 agent_skills 表
**任务 ID**: AGENT-001-T03
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- agent_profiles 表已创建

**执行步骤**:
1. 执行 SQL 创建 agent_skills 表
2. 创建复合主键（agent_id, skill_name）
3. 创建索引（agent_id）

**输出**:
- agent_skills 表创建成功

**验证方法**:
```sql
\d agent_skills
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS agent_skills;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 复合主键正确
- [ ] 索引创建成功

---

### 任务 19: 创建 agent_performance 表
**任务 ID**: AGENT-001-T04
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- agent_profiles 表已创建

**执行步骤**:
1. 执行 SQL 创建 agent_performance 表
2. 创建外键（agent_id）
3. 创建索引（agent_id, action_time）

**输出**:
- agent_performance 表创建成功

**验证方法**:
```sql
\d agent_performance
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS agent_performance;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### 任务 20: 实现 Agency 定义加载
**任务 ID**: AGENT-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- agencies 表已创建
- Python 环境

**执行步骤**:
1. 创建 services/agency_loader.py
2. 实现 load_agencies 函数
3. 实现 load_agency_by_name 函数
4. 实现缓存机制

**输出**:
- services/agency_loader.py 文件
- 2 个加载函数

**验证方法**:
```python
from services.agency_loader import load_agencies
agencies = load_agencies()
assert len(agencies) == 5
```

**回滚方案**:
```bash
rm services/agency_loader.py
```

**验收标准**:
- [ ] Agency 加载成功
- [ ] 缓存生效

---

### 任务 21: 实现 Agent 档案管理
**任务 ID**: AGENT-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- services/agency_loader.py 已创建

**执行步骤**:
1. 创建 services/agent_manager.py
2. 实现 create_agent 函数
3. 实现 get_agent 函数
4. 实现 update_agent 函数

**输出**:
- services/agent_manager.py 文件
- 3 个管理函数

**验证方法**:
```python
from services.agent_manager import create_agent
agent = create_agent("developer", "user_id")
assert agent["agency"] == "developer"
```

**回滚方案**:
```bash
rm services/agent_manager.py
```

**验收标准**:
- [ ] Agent 创建成功
- [ ] Agent 查询成功
- [ ] Agent 更新成功

---

### 任务 22: 实现技能掌握度追踪
**任务 ID**: AGENT-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- agent_skills 表已创建

**执行步骤**:
1. 实现 record_skill_usage 函数
2. 实现 get_skill_level 函数
3. 实现 update_skill_level 函数

**输出**:
- 3 个技能追踪函数

**验证方法**:
```python
from services.agent_manager import record_skill_usage
record_skill_usage("agent_id", "python", 1.0)
level = get_skill_level("agent_id", "python")
assert level >= 1
```

**回滚方案**:
```bash
# 回滚 agent_manager.py
git checkout HEAD~1 services/agent_manager.py
```

**验收标准**:
- [ ] 技能使用记录成功
- [ ] 技能等级查询成功
- [ ] 技能等级更新成功

---

### 任务 23: 实现经验值系统
**任务 ID**: AGENT-001-T08
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- agent_profiles 表已创建

**执行步骤**:
1. 实现 add_experience 函数
2. 实现 get_experience 函数
3. 实现 check_level_up 函数

**输出**:
- 3 个经验值函数

**验证方法**:
```python
from services.agent_manager import add_experience
add_experience("agent_id", 100)
exp = get_experience("agent_id")
assert exp >= 100
```

**回滚方案**:
```bash
# 回滚经验值函数
```

**验收标准**:
- [ ] 经验值添加成功
- [ ] 经验值查询成功
- [ ] 等级检查成功

---

### 任务 24: 实现智能匹配算法
**任务 ID**: AGENT-001-T09
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- agent_profiles 表已创建
- agent_skills 表已创建

**执行步骤**:
1. 创建 services/agent_matcher.py
2. 实现 calculate_skill_match 函数
3. 实现 calculate_experience_score 函数
4. 实现 calculate_performance_score 函数
5. 实现 match_agent_to_task 函数

**输出**:
- services/agent_matcher.py 文件
- 5 个匹配函数

**验证方法**:
```python
from services.agent_matcher import match_agent_to_task
task = {"required_skills": ["python", "fastapi"]}
agent, score = match_agent_to_task(task)
assert score > 0.7
```

**回滚方案**:
```bash
rm services/agent_matcher.py
```

**验收标准**:
- [ ] 技能匹配计算正确
- [ ] 经验值评分正确
- [ ] 绩效评分正确
- [ ] 返回最佳匹配

---

### 任务 25: 实现 Agent 分配 API
**任务 ID**: AGENT-001-T10
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- services/agent_matcher.py 已创建
- FastAPI 环境

**执行步骤**:
1. 创建 api/agents.py
2. 实现 POST /api/agents/assign 端点
3. 调用 matcher 服务
4. 返回分配的 Agent

**输出**:
- api/agents.py 文件
- POST /api/agents/assign 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/agents/assign \
  -H "Content-Type: application/json" \
  -d '{"task_id":"uuid","required_skills":["python"]}'
```

**回滚方案**:
```bash
rm api/agents.py
```

**验收标准**:
- [ ] Agent 分配成功
- [ ] 返回最佳匹配
- [ ] 分配记录保存

---

### 任务 26: 实现 Agent 状态查询 API
**任务 ID**: AGENT-001-T11
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- api/agents.py 已创建

**执行步骤**:
1. 实现 GET /api/agents 端点
2. 实现 GET /api/agents/{agent_id} 端点
3. 实现状态过滤（idle/busy）

**输出**:
- GET /api/agents 端点
- GET /api/agents/{agent_id} 端点

**验证方法**:
```bash
curl http://localhost:8000/api/agents?status=idle
```

**回滚方案**:
```bash
# 注释掉端点
```

**验收标准**:
- [ ] Agent 列表查询成功
- [ ] Agent 详情查询成功
- [ ] 状态过滤生效

---

### 任务 27: 实现 Agent 档案 API
**任务 ID**: AGENT-001-T12
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- api/agents.py 已创建

**执行步骤**:
1. 实现 GET /api/agents/{agent_id}/profile 端点
2. 实现 GET /api/agents/{agent_id}/skills 端点
3. 实现 GET /api/agents/{agent_id}/performance 端点

**输出**:
- 3 个档案查询端点

**验证方法**:
```bash
curl http://localhost:8000/api/agents/uuid/profile
```

**回滚方案**:
```bash
# 注释掉端点
```

**验收标准**:
- [ ] 档案查询成功
- [ ] 技能列表查询成功
- [ ] 绩效历史查询成功

---

### 任务 28: 编写 Agency-Agent 单元测试
**任务 ID**: AGENT-001-T13
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 所有 Agency-Agent 代码已完成

**执行步骤**:
1. 创建 tests/test_agents.py
2. 编写 Agency 加载测试
3. 编写 Agent 管理测试
4. 编写智能匹配测试
5. 运行测试

**输出**:
- tests/test_agents.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_agents.py -v
```

**回滚方案**:
```bash
rm tests/test_agents.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

## 阶段二-3：评审与质量保证（第 3 周，05-16 至 05-22）

### 任务 29: 创建 reviews 表
**任务 ID**: REVIEW-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- PostgreSQL 数据库连接

**执行步骤**:
1. 执行 SQL 创建 reviews 表
2. 创建外键（task_id, reviewer_id）
3. 创建索引（task_id, status）

**输出**:
- reviews 表创建成功

**验证方法**:
```sql
\d reviews
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS reviews;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### 任务 30: 创建 review_items 表
**任务 ID**: REVIEW-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- reviews 表已创建

**执行步骤**:
1. 执行 SQL 创建 review_items 表
2. 创建外键（review_id）
3. 创建索引（review_id）

**输出**:
- review_items 表创建成功

**验证方法**:
```sql
\d review_items
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS review_items;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效

---

### 任务 31: 实现评审创建 API
**任务 ID**: REVIEW-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- reviews 表已创建
- FastAPI 环境

**执行步骤**:
1. 创建 api/reviews.py
2. 实现 POST /api/reviews 端点
3. 实现自动分配评审人逻辑

**输出**:
- api/reviews.py 文件
- POST /api/reviews 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"task_id":"uuid","reviewer_id":"uuid"}'
```

**回滚方案**:
```bash
rm api/reviews.py
```

**验收标准**:
- [ ] 评审创建成功
- [ ] 评审人分配成功

---

### 任务 32: 实现评审提交 API
**任务 ID**: REVIEW-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- api/reviews.py 已创建

**执行步骤**:
1. 实现 POST /api/reviews/{review_id}/submit 端点
2. 实现评分逻辑
3. 实现评审项记录

**输出**:
- POST /api/reviews/{review_id}/submit 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/reviews/uuid/submit \
  -H "Content-Type: application/json" \
  -d '{"score":90,"items":[...]}'
```

**回滚方案**:
```bash
# 注释掉 submit 端点
```

**验收标准**:
- [ ] 评审提交成功
- [ ] 评分记录成功
- [ ] 评审项记录成功

---

### 任务 33: 实现评审结果处理
**任务 ID**: REVIEW-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- api/reviews.py 已创建

**执行步骤**:
1. 实现 handle_review_pass 函数
2. 实现 handle_review_fail 函数
3. 实现 create_rework_task 函数

**输出**:
- 3 个结果处理函数

**验证方法**:
```python
from api.reviews import handle_review_fail
handle_review_fail("review_id", "需要修改")
```

**回滚方案**:
```bash
# 回滚结果处理函数
```

**验收标准**:
- [ ] 通过处理正确
- [ ] 失败处理正确
- [ ] 返工任务创建成功

---

### 任务 34: 实现 Bug 跟踪表
**任务 ID**: BUG-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- PostgreSQL 数据库连接

**执行步骤**:
1. 执行 SQL 创建 bugs 表
2. 创建外键（project_id, reporter_id, assignee_id）
3. 创建索引（status, priority, created_at）

**输出**:
- bugs 表创建成功

**验证方法**:
```sql
\d bugs
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS bugs;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### 任务 35: 实现 Bug 提交 API
**任务 ID**: BUG-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- bugs 表已创建
- FastAPI 环境

**执行步骤**:
1. 实现 POST /api/bugs 端点
2. 实现自动分配逻辑
3. 实现通知逻辑

**输出**:
- POST /api/bugs 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/bugs \
  -H "Content-Type: application/json" \
  -d '{"title":"Bug 标题","description":"描述","priority":"high"}'
```

**回滚方案**:
```bash
# 注释掉端点
```

**验收标准**:
- [ ] Bug 提交成功
- [ ] 自动分配成功
- [ ] 通知发送成功

---

### 任务 36: 实现 Bug 状态更新 API
**任务 ID**: BUG-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- POST /api/bugs 已创建

**执行步骤**:
1. 实现 PUT /api/bugs/{bug_id}/status 端点
2. 实现状态流转逻辑（open → in_progress → resolved → closed）
3. 实现状态变更历史

**输出**:
- PUT /api/bugs/{bug_id}/status 端点

**验证方法**:
```bash
curl -X PUT http://localhost:8000/api/bugs/uuid/status \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'
```

**回滚方案**:
```bash
# 注释掉端点
```

**验收标准**:
- [ ] 状态更新成功
- [ ] 状态流转正确
- [ ] 历史记录保存

---

### 任务 37: 实现 Bug 统计分析 API
**任务 ID**: BUG-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- bugs 表已创建

**执行步骤**:
1. 实现 GET /api/bugs/stats 端点
2. 实现按状态统计
3. 实现按优先级统计
4. 实现趋势分析

**输出**:
- GET /api/bugs/stats 端点

**验证方法**:
```bash
curl http://localhost:8000/api/bugs/stats
```

**回滚方案**:
```bash
# 注释掉端点
```

**验收标准**:
- [ ] 统计数据正确
- [ ] 趋势分析正确

---

### 任务 38: 创建用户管理系统模板
**任务 ID**: DEMO-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 模板系统已完成
- Agency-Agent 系统已完成

**执行步骤**:
1. 创建 templates/user-management-system.yaml
2. 定义 5 个 Phase（需求、设计、开发、测试、验收）
3. 定义每个 Phase 的 Agent 角色
4. 通过 API 导入模板

**输出**:
- templates/user-management-system.yaml 文件

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/templates ...
```

**回滚方案**:
```bash
rm templates/user-management-system.yaml
```

**验收标准**:
- [ ] 模板定义完整
- [ ] Phase 定义正确
- [ ] Agent 角色分配正确

---

### 任务 39: 执行用户管理系统演示
**任务 ID**: DEMO-001-T02
**预计时长**: 15 分钟
**负责人**: 全员

**输入**:
- 用户管理系统模板已创建

**执行步骤**:
1. 创建项目（使用用户管理系统模板）
2. 执行需求 Phase
3. 执行设计 Phase
4. 执行开发 Phase
5. 执行测试 Phase
6. 执行验收 Phase

**输出**:
- 项目执行记录
- 各 Phase 产出物

**验证方法**:
```bash
curl http://localhost:8000/api/projects/uuid/status
```

**回滚方案**:
```bash
# 删除测试项目
curl -X DELETE http://localhost:8000/api/projects/uuid
```

**验收标准**:
- [ ] 所有 Phase 执行成功
- [ ] 产出物完整
- [ ] 评审流程正常

---

### 任务 40: 录制演示视频
**任务 ID**: DEMO-001-T03
**预计时长**: 15 分钟
**负责人**: 全员

**输入**:
- 用户管理系统演示已完成

**执行步骤**:
1. 使用录屏软件录制演示过程
2. 录制 Dashboard 监控画面
3. 剪辑视频（可选）
4. 保存视频文件

**输出**:
- demos/user-management-system-demo.mp4 文件

**验证方法**:
```bash
ls -lh demos/user-management-system-demo.mp4
```

**回滚方案**:
```bash
rm demos/user-management-system-demo.mp4
```

**验收标准**:
- [ ] 视频完整
- [ ] 画面清晰
- [ ] 时长<5 分钟

---

### 任务 41: 编写阶段二测试报告
**任务 ID**: DEMO-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有测试已完成

**执行步骤**:
1. 汇总所有测试结果
2. 计算覆盖率
3. 编写测试报告
4. 保存报告

**输出**:
- reports/phase2-test-report.md 文件

**验证方法**:
```bash
cat reports/phase2-test-report.md
```

**回滚方案**:
```bash
rm reports/phase2-test-report.md
```

**验收标准**:
- [ ] 测试结果完整
- [ ] 覆盖率统计正确
- [ ] 问题列表清晰

---

### 任务 42: 阶段二复审
**任务 ID**: DEMO-001-T05
**预计时长**: 15 分钟
**负责人**: 评审组

**输入**:
- 所有阶段二任务已完成
- 演示视频已录制
- 测试报告已编写

**执行步骤**:
1. 准备复审材料
2. 演示用户管理系统
3. 评审组提问
4. 评审组签字

**输出**:
- reviews/phase2-review-report.md 文件
- 评审组签字

**验证方法**:
```bash
cat reviews/phase2-review-report.md
```

**回滚方案**:
```bash
# 不适用
```

**验收标准**:
- [ ] 评审组通过
- [ ] 所有问题已回答
- [ ] 签字确认

---

## 阶段二总结

**总任务数**: 42 个
**总工时**: 10.5 小时（42 × 15 分钟）
**完成率**: 0/42

**关键路径**:
1. 数据库表创建（T01-T04, T16-T19, T29-T30, T34）
2. 模板系统（T04-T15）
3. Agency-Agent（T20-T28）
4. 评审系统（T31-T33）
5. Bug 工作流（T35-T37）
6. 演示准备（T38-T42）

**依赖关系**:
```
数据库表 → 模板系统 → Agency-Agent → 评审系统 → Bug 工作流 → 演示
```

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：待执行*
