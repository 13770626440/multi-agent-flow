# 阶段三：自反馈优化 - 详细任务表

## 阶段信息
- **阶段名称**: 自反馈优化
- **工期**: 2 周（2026-05-23 至 06-05）
- **目标**: 自动复盘优化系统，Skill 知识库管理，闭环优化工作流
- **总任务数**: 30 个
- **单任务时长**: ≤15 分钟

---

## 阶段三 -1：Metrics 收集系统（第 1 周，05-23 至 05-29）

### 任务 1: 创建 metrics_configs 表
**任务 ID**: METRICS-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- PostgreSQL 数据库连接

**执行步骤**:
1. 执行 SQL 创建 metrics_configs 表
2. 定义指标配置字段（name, description, unit, target）
3. 创建索引（name）

**输出**:
- metrics_configs 表创建成功

**验证方法**:
```sql
\d metrics_configs
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS metrics_configs;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 索引创建成功

---

### 任务 2: 创建 project_metrics_data 表
**任务 ID**: METRICS-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- metrics_configs 表已创建
- projects 表已创建

**执行步骤**:
1. 执行 SQL 创建 project_metrics_data 表
2. 创建外键（project_id, metric_id）
3. 创建索引（project_id, action_time）

**输出**:
- project_metrics_data 表创建成功

**验证方法**:
```sql
\d project_metrics_data
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS project_metrics_data;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效

---

### 任务 3: 实现 Metrics 收集服务
**任务 ID**: METRICS-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- project_metrics_data 表已创建

**执行步骤**:
1. 创建 services/metrics_collector.py
2. 实现 collect_project_metrics 函数
3. 实现 collect_phase_metrics 函数
4. 实现 collect_task_metrics 函数

**输出**:
- services/metrics_collector.py 文件
- 3 个收集函数

**验证方法**:
```python
from services.metrics_collector import collect_project_metrics
metrics = collect_project_metrics("project_id")
assert "duration" in metrics
```

**回滚方案**:
```bash
rm services/metrics_collector.py
```

**验收标准**:
- [ ] 项目指标收集成功
- [ ] Phase 指标收集成功
- [ ] Task 指标收集成功

---

### 任务 4: 实现 OpenMOSS Metrics 收集
**任务 ID**: METRICS-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- metrics_collector.py 已创建
- OpenMOSS API 客户端已创建

**执行步骤**:
1. 实现 collect_from_openmoss 函数
2. 调用 OpenMOSS API 获取 metrics
3. 解析响应数据
4. 存储到数据库

**输出**:
- collect_from_openmoss 函数

**验证方法**:
```python
from services.metrics_collector import collect_from_openmoss
metrics = collect_from_openmoss("project_id")
assert len(metrics) > 0
```

**回滚方案**:
```bash
# 回滚 collect_from_openmoss 函数
git checkout HEAD~1 services/metrics_collector.py
```

**验收标准**:
- [ ] OpenMOSS Metrics 收集成功
- [ ] 数据解析正确
- [ ] 存储成功

---

### 任务 5: 实现 Metrics 清洗服务
**任务 ID**: METRICS-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Metrics 收集服务已创建

**执行步骤**:
1. 创建 services/metrics_cleaner.py
2. 实现 clean_metrics 函数
3. 实现 normalize_metrics 函数
4. 实现 validate_metrics 函数

**输出**:
- services/metrics_cleaner.py 文件
- 3 个清洗函数

**验证方法**:
```python
from services.metrics_cleaner import clean_metrics
raw_metrics = {"duration": "120s"}
cleaned = clean_metrics(raw_metrics)
assert cleaned["duration"] == 120
```

**回滚方案**:
```bash
rm services/metrics_cleaner.py
```

**验收标准**:
- [ ] 数据清洗正确
- [ ] 标准化正确
- [ ] 验证正确

---

### 任务 6: 创建 Metrics API
**任务 ID**: METRICS-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Metrics 收集服务已创建
- FastAPI 环境

**执行步骤**:
1. 创建 api/metrics.py
2. 实现 GET /api/metrics/{project_id} 端点
3. 实现 GET /api/metrics/{project_id}/timeline 端点
4. 实现 POST /api/metrics/collect 端点

**输出**:
- api/metrics.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl http://localhost:8000/api/metrics/project_uuid
```

**回滚方案**:
```bash
rm api/metrics.py
```

**验收标准**:
- [ ] Metrics 查询成功
- [ ] 时间线查询成功
- [ ] 手动收集成功

---

### 任务 7: 实现 Metrics 定时收集
**任务 ID**: METRICS-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Metrics API 已创建

**执行步骤**:
1. 安装 APScheduler：`pip install apscheduler`
2. 创建 schedulers/metrics_scheduler.py
3. 实现定时收集任务（每 5 分钟）
4. 启动调度器

**输出**:
- schedulers/metrics_scheduler.py 文件
- 定时收集任务

**验证方法**:
```python
from schedulers.metrics_scheduler import start_scheduler
start_scheduler()
# 等待 5 分钟，检查数据库是否有新数据
```

**回滚方案**:
```bash
rm schedulers/metrics_scheduler.py
```

**验收标准**:
- [ ] 定时任务启动成功
- [ ] 每 5 分钟收集一次
- [ ] 数据正确存储

---

### 任务 8: 编写 Metrics 测试
**任务 ID**: METRICS-001-T08
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有 Metrics 代码已完成

**执行步骤**:
1. 创建 tests/test_metrics.py
2. 编写收集测试
3. 编写清洗测试
4. 编写 API 测试
5. 运行测试

**输出**:
- tests/test_metrics.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_metrics.py -v
```

**回滚方案**:
```bash
rm tests/test_metrics.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

## 阶段三 -2：复盘分析引擎（第 1 周，05-23 至 05-29）

### 任务 9: 创建 review_reports 表
**任务 ID**: REVIEW-ANA-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- PostgreSQL 数据库连接
- projects 表已创建

**执行步骤**:
1. 执行 SQL 创建 review_reports 表
2. 创建外键（project_id）
3. 创建索引（project_id, created_at）

**输出**:
- review_reports 表创建成功

**验证方法**:
```sql
\d review_reports
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS review_reports;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效

---

### 任务 10: 创建 improvement_suggestions 表
**任务 ID**: REVIEW-ANA-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- review_reports 表已创建

**执行步骤**:
1. 执行 SQL 创建 improvement_suggestions 表
2. 创建外键（review_report_id）
3. 创建索引（review_report_id, priority）

**输出**:
- improvement_suggestions 表创建成功

**验证方法**:
```sql
\d improvement_suggestions
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS improvement_suggestions;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效

---

### 任务 11: 实现根因分析算法
**任务 ID**: REVIEW-ANA-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Metrics 数据已收集

**执行步骤**:
1. 创建 services/root_cause_analyzer.py
2. 实现 analyze_delays 函数（分析延期原因）
3. 实现 analyze_quality_issues 函数（分析质量问题）
4. 实现 analyze_resource_issues 函数（分析资源问题）

**输出**:
- services/root_cause_analyzer.py 文件
- 3 个分析函数

**验证方法**:
```python
from services.root_cause_analyzer import analyze_delays
causes = analyze_delays("project_id")
assert len(causes) > 0
```

**回滚方案**:
```bash
rm services/root_cause_analyzer.py
```

**验收标准**:
- [ ] 延期分析正确
- [ ] 质量问题分析正确
- [ ] 资源问题分析正确

---

### 任务 12: 实现历史基准对比
**任务 ID**: REVIEW-ANA-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- root_cause_analyzer.py 已创建

**执行步骤**:
1. 实现 compare_with_baseline 函数
2. 查询历史项目数据
3. 计算平均值和标准差
4. 返回对比结果

**输出**:
- compare_with_baseline 函数

**验证方法**:
```python
from services.root_cause_analyzer import compare_with_baseline
comparison = compare_with_baseline("project_id", "duration")
assert "current" in comparison
assert "average" in comparison
```

**回滚方案**:
```bash
# 回滚 compare_with_baseline 函数
git checkout HEAD~1 services/root_cause_analyzer.py
```

**验收标准**:
- [ ] 历史数据查询正确
- [ ] 对比计算正确
- [ ] 结果格式正确

---

### 任务 13: 实现问题识别算法
**任务 ID**: REVIEW-ANA-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 根因分析已完成
- 历史基准对比已完成

**执行步骤**:
1. 实现 identify_patterns 函数
2. 识别常见问题模式
3. 识别异常模式
4. 返回问题列表

**输出**:
- identify_patterns 函数

**验证方法**:
```python
from services.root_cause_analyzer import identify_patterns
patterns = identify_patterns("project_id")
assert len(patterns) > 0
```

**回滚方案**:
```bash
# 回滚 identify_patterns 函数
```

**验收标准**:
- [ ] 问题模式识别正确
- [ ] 异常模式识别正确

---

### 任务 14: 创建复盘报告 API
**任务 ID**: REVIEW-ANA-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 根因分析已完成
- FastAPI 环境

**执行步骤**:
1. 创建 api/review_reports.py
2. 实现 POST /api/review-reports 端点
3. 实现 GET /api/review-reports/{report_id} 端点
4. 实现分析逻辑

**输出**:
- api/review_reports.py 文件
- 2 个 API 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/review-reports \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid"}'
```

**回滚方案**:
```bash
rm api/review_reports.py
```

**验收标准**:
- [ ] 复盘报告创建成功
- [ ] 报告查询成功

---

### 任务 15: 编写复盘分析测试
**任务 ID**: REVIEW-ANA-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 所有复盘分析代码已完成

**执行步骤**:
1. 创建 tests/test_review_analysis.py
2. 编写根因分析测试
3. 编写基准对比测试
4. 编写问题识别测试
5. 运行测试

**输出**:
- tests/test_review_analysis.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_review_analysis.py -v
```

**回滚方案**:
```bash
rm tests/test_review_analysis.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

## 阶段三 -3：模板优化工作流（第 2 周，05-30 至 06-05）

### 任务 16: 实现优化建议生成
**任务 ID**: OPT-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 复盘分析已完成

**执行步骤**:
1. 创建 services/optimization_generator.py
2. 实现 generate_suggestions 函数
3. 实现 prioritize_suggestions 函数
4. 实现 estimate_impact 函数

**输出**:
- services/optimization_generator.py 文件
- 3 个生成函数

**验证方法**:
```python
from services.optimization_generator import generate_suggestions
suggestions = generate_suggestions("review_report_id")
assert len(suggestions) > 0
```

**回滚方案**:
```bash
rm services/optimization_generator.py
```

**验收标准**:
- [ ] 优化建议生成成功
- [ ] 优先级排序正确
- [ ] 影响评估正确

---

### 任务 17: 实现模板优化草案
**任务 ID**: OPT-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 优化建议生成已完成
- 模板系统已完成

**执行步骤**:
1. 实现 create_template_draft 函数
2. 基于优化建议修改模板
3. 生成新版本草案
4. 保存草案

**输出**:
- create_template_draft 函数

**验证方法**:
```python
from services.optimization_generator import create_template_draft
draft = create_template_draft("template_id", ["suggestion1"])
assert draft["version"] == "1.1"
```

**回滚方案**:
```bash
# 回滚 create_template_draft 函数
git checkout HEAD~1 services/optimization_generator.py
```

**验收标准**:
- [ ] 草案创建成功
- [ ] 版本号正确
- [ ] 优化建议已应用

---

### 任务 18: 实现人工确认流程
**任务 ID**: OPT-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 模板优化草案已完成

**执行步骤**:
1. 实现 request_approval 函数
2. 实现 approve_template 函数
3. 实现 reject_template 函数
4. 创建审批通知

**输出**:
- 3 个审批函数

**验证方法**:
```python
from services.optimization_generator import request_approval
request_approval("draft_id", "admin_user_id")
```

**回滚方案**:
```bash
# 回滚审批函数
```

**验收标准**:
- [ ] 审批请求成功
- [ ] 批准成功
- [ ] 拒绝成功

---

### 任务 19: 实现模板发布
**任务 ID**: OPT-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 人工确认流程已完成

**执行步骤**:
1. 实现 publish_template 函数
2. 更新模板状态为 published
3. 记录版本历史
4. 通知用户

**输出**:
- publish_template 函数

**验证方法**:
```python
from services.optimization_generator import publish_template
publish_template("draft_id")
```

**回滚方案**:
```bash
# 回滚发布函数
```

**验收标准**:
- [ ] 模板发布成功
- [ ] 状态更新正确
- [ ] 历史记录保存

---

### 任务 20: 创建优化 API
**任务 ID**: OPT-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 模板优化工作流已完成

**执行步骤**:
1. 创建 api/optimizations.py
2. 实现 POST /api/optimizations/generate 端点
3. 实现 POST /api/optimizations/approve 端点
4. 实现 GET /api/optimizations/history 端点

**输出**:
- api/optimizations.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/optimizations/generate \
  -H "Content-Type: application/json" \
  -d '{"review_report_id":"uuid"}'
```

**回滚方案**:
```bash
rm api/optimizations.py
```

**验收标准**:
- [ ] 优化生成成功
- [ ] 审批成功
- [ ] 历史查询成功

---

### 任务 21: 编写优化测试
**任务 ID**: OPT-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有优化代码已完成

**执行步骤**:
1. 创建 tests/test_optimizations.py
2. 编写建议生成测试
3. 编写草案创建测试
4. 编写审批流程测试
5. 运行测试

**输出**:
- tests/test_optimizations.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_optimizations.py -v
```

**回滚方案**:
```bash
rm tests/test_optimizations.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

## 阶段三 -4：Skill 沉淀系统（第 2 周，05-30 至 06-05）

### 任务 22: 创建 skills 表
**任务 ID**: SKILL-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- PostgreSQL 数据库连接

**执行步骤**:
1. 执行 SQL 创建 skills 表
2. 定义 Skill 字段（name, description, content, category）
3. 创建索引（name, category）

**输出**:
- skills 表创建成功

**验证方法**:
```sql
\d skills
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS skills;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 索引创建成功

---

### 任务 23: 创建 skill_usage_logs 表
**任务 ID**: SKILL-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 B

**输入**:
- skills 表已创建

**执行步骤**:
1. 执行 SQL 创建 skill_usage_logs 表
2. 创建外键（skill_id）
3. 创建索引（skill_id, used_at）

**输出**:
- skill_usage_logs 表创建成功

**验证方法**:
```sql
\d skill_usage_logs
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS skill_usage_logs;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效

---

### 任务 24: 实现 Skill 提取服务
**任务 ID**: SKILL-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- skills 表已创建
- 复盘分析已完成

**执行步骤**:
1. 创建 services/skill_extractor.py
2. 实现 extract_from_review 函数
3. 实现 extract_from_optimization 函数
4. 实现 normalize_skill 函数

**输出**:
- services/skill_extractor.py 文件
- 3 个提取函数

**验证方法**:
```python
from services.skill_extractor import extract_from_review
skill = extract_from_review("review_report_id")
assert "name" in skill
```

**回滚方案**:
```bash
rm services/skill_extractor.py
```

**验收标准**:
- [ ] Skill 提取成功
- [ ] 标准化正确

---

### 任务 25: 实现 Skill 存储
**任务 ID**: SKILL-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Skill 提取服务已完成

**执行步骤**:
1. 实现 store_skill 函数
2. 实现 Skill 去重逻辑
3. 实现 Skill 分类
4. 存储到数据库

**输出**:
- store_skill 函数

**验证方法**:
```python
from services.skill_extractor import store_skill
skill_id = store_skill(skill_data)
assert skill_id is not None
```

**回滚方案**:
```bash
# 回滚 store_skill 函数
git checkout HEAD~1 services/skill_extractor.py
```

**验收标准**:
- [ ] Skill 存储成功
- [ ] 去重正确
- [ ] 分类正确

---

### 任务 26: 实现 Skill 匹配服务
**任务 ID**: SKILL-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Skill 存储已完成

**执行步骤**:
1. 创建 services/skill_matcher.py
2. 实现 match_skills 函数
3. 实现 calculate_relevance 函数
4. 实现 rank_skills 函数

**输出**:
- services/skill_matcher.py 文件
- 3 个匹配函数

**验证方法**:
```python
from services.skill_matcher import match_skills
skills = match_skills("project_context")
assert len(skills) > 0
```

**回滚方案**:
```bash
rm services/skill_matcher.py
```

**验收标准**:
- [ ] Skill 匹配成功
- [ ] 相关性计算正确
- [ ] 排序正确

---

### 任务 27: 实现 Skill 注入
**任务 ID**: SKILL-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Skill 匹配服务已完成
- Agent 系统已完成

**执行步骤**:
1. 实现 inject_skills 函数
2. 实现 Skill 上下文构建
3. 注入到 Agent 配置

**输出**:
- inject_skills 函数

**验证方法**:
```python
from services.skill_matcher import inject_skills
inject_skills("agent_id", ["skill1", "skill2"])
```

**回滚方案**:
```bash
# 回滚 inject_skills 函数
```

**验收标准**:
- [ ] Skill 注入成功
- [ ] 上下文构建正确

---

### 任务 28: 创建 Skill API
**任务 ID**: SKILL-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Skill 服务已完成
- FastAPI 环境

**执行步骤**:
1. 创建 api/skills.py
2. 实现 GET /api/skills 端点
3. 实现 POST /api/skills/extract 端点
4. 实现 GET /api/skills/match 端点

**输出**:
- api/skills.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl http://localhost:8000/api/skills
```

**回滚方案**:
```bash
rm api/skills.py
```

**验收标准**:
- [ ] Skill 列表查询成功
- [ ] Skill 提取成功
- [ ] Skill 匹配成功

---

### 任务 29: 实现 Skill 效果追踪
**任务 ID**: SKILL-001-T08
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Skill API 已创建

**执行步骤**:
1. 实现 track_skill_usage 函数
2. 实现 calculate_effectiveness 函数
3. 实现 Skill 淘汰机制

**输出**:
- 3 个追踪函数

**验证方法**:
```python
from services.skill_matcher import track_skill_usage
track_skill_usage("skill_id", "project_id", True)
```

**回滚方案**:
```bash
# 回滚追踪函数
```

**验收标准**:
- [ ] 使用记录成功
- [ ] 效果计算正确
- [ ] 淘汰机制正确

---

### 任务 30: 编写 Skill 测试
**任务 ID**: SKILL-001-T09
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 所有 Skill 代码已完成

**执行步骤**:
1. 创建 tests/test_skills.py
2. 编写 Skill 提取测试
3. 编写 Skill 匹配测试
4. 编写 Skill 注入测试
5. 运行测试

**输出**:
- tests/test_skills.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_skills.py -v
```

**回滚方案**:
```bash
rm tests/test_skills.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

## 阶段三总结

**总任务数**: 30 个
**总工时**: 7.5 小时（30 × 15 分钟）
**完成率**: 0/30

**关键路径**:
1. Metrics 收集（T01-T08）
2. 复盘分析（T09-T15）
3. 模板优化（T16-T21）
4. Skill 沉淀（T22-T30）

**依赖关系**:
```
Metrics 收集 → 复盘分析 → 模板优化
                    ↓
                Skill 沉淀
```

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：待执行*
