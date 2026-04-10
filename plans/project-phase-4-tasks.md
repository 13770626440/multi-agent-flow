# 阶段四：Dashboard 增强 - 详细任务表

## 阶段信息
- **阶段名称**: Dashboard 增强
- **工期**: 1-2 周（2026-06-06 至 06-19）
- **目标**: 完整 Web Dashboard，用户友好的管理界面，部署包和文档
- **总任务数**: 30 个
- **单任务时长**: ≤15 分钟

---

## 阶段四 -1：项目管理界面（第 1 周，06-06 至 06-12）

### 任务 1: 创建项目列表组件
**任务 ID**: DASH-PROJ-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Vue 3 环境
- Element Plus 已安装

**执行步骤**:
1. 创建 src/views/projects/ProjectList.vue 组件
2. 使用 el-table 显示项目列表
3. 添加分页功能
4. 添加搜索框

**输出**:
- src/views/projects/ProjectList.vue 文件

**验证方法**:
```bash
cat src/views/projects/ProjectList.vue
```

**回滚方案**:
```bash
rm src/views/projects/ProjectList.vue
```

**验收标准**:
- [ ] 项目列表显示正常
- [ ] 分页功能正常
- [ ] 搜索功能正常

---

### 任务 2: 实现项目创建向导
**任务 ID**: DASH-PROJ-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- ProjectList.vue 已创建

**执行步骤**:
1. 创建 src/views/projects/CreateProject.vue 组件
2. 使用 el-steps 实现向导
3. 第一步：选择模板
4. 第二步：填写信息
5. 第三步：确认创建

**输出**:
- src/views/projects/CreateProject.vue 文件

**验证方法**:
```bash
cat src/views/projects/CreateProject.vue
```

**回滚方案**:
```bash
rm src/views/projects/CreateProject.vue
```

**验收标准**:
- [ ] 向导步骤显示正常
- [ ] 模板选择正常
- [ ] 表单验证正常

---

### 任务 3: 实现项目详情页面
**任务 ID**: DASH-PROJ-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- CreateProject.vue 已创建

**执行步骤**:
1. 创建 src/views/projects/ProjectDetail.vue 组件
2. 显示项目基本信息
3. 显示项目进度
4. 显示 Phase 列表

**输出**:
- src/views/projects/ProjectDetail.vue 文件

**验证方法**:
```bash
cat src/views/projects/ProjectDetail.vue
```

**回滚方案**:
```bash
rm src/views/projects/ProjectDetail.vue
```

**验收标准**:
- [ ] 项目信息显示正常
- [ ] 进度显示正常
- [ ] Phase 列表显示正常

---

### 任务 4: 实现项目进度可视化
**任务 ID**: DASH-PROJ-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- ProjectDetail.vue 已创建
- ECharts 已安装

**执行步骤**:
1. 安装 ECharts：`npm install echarts`
2. 创建 src/components/ProjectProgress.vue 组件
3. 使用 ECharts 绘制进度图
4. 显示各 Phase 进度

**输出**:
- src/components/ProjectProgress.vue 文件

**验证方法**:
```bash
cat src/components/ProjectProgress.vue
```

**回滚方案**:
```bash
rm src/components/ProjectProgress.vue
```

**验收标准**:
- [ ] ECharts 图表显示正常
- [ ] 进度数据正确
- [ ] 交互正常

---

### 任务 5: 实现项目状态跟踪
**任务 ID**: DASH-PROJ-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- ProjectProgress.vue 已创建

**执行步骤**:
1. 创建 src/components/ProjectTimeline.vue 组件
2. 使用时间线显示项目历史
3. 显示关键事件
4. 显示状态变更

**输出**:
- src/components/ProjectTimeline.vue 文件

**验证方法**:
```bash
cat src/components/ProjectTimeline.vue
```

**回滚方案**:
```bash
rm src/components/ProjectTimeline.vue
```

**验收标准**:
- [ ] 时间线显示正常
- [ ] 事件显示正常
- [ ] 状态变更显示正常

---

### 任务 6: 实现项目成员管理
**任务 ID**: DASH-PROJ-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- ProjectDetail.vue 已创建

**执行步骤**:
1. 创建 src/components/ProjectMembers.vue 组件
2. 显示成员列表
3. 实现添加成员功能
4. 实现移除成员功能

**输出**:
- src/components/ProjectMembers.vue 文件

**验证方法**:
```bash
cat src/components/ProjectMembers.vue
```

**回滚方案**:
```bash
rm src/components/ProjectMembers.vue
```

**验收标准**:
- [ ] 成员列表显示正常
- [ ] 添加成员正常
- [ ] 移除成员正常

---

### 任务 7: 实现项目操作 API
**任务 ID**: DASH-PROJ-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 前端项目组件已创建
- FastAPI 环境

**执行步骤**:
1. 创建 code/backend/api/projects_frontend.py
2. 实现 GET /api/frontend/projects 端点
3. 实现 POST /api/frontend/projects 端点
4. 实现 GET /api/frontend/projects/{id} 端点

**输出**:
- code/backend/api/projects_frontend.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl http://localhost:8000/api/frontend/projects
```

**回滚方案**:
```bash
rm code/backend/api/projects_frontend.py
```

**验收标准**:
- [ ] 项目列表 API 正常
- [ ] 创建项目 API 正常
- [ ] 项目详情 API 正常

---

## 阶段四 -2：模板管理界面（第 1 周，06-06 至 06-12）

### 任务 8: 创建模板列表组件
**任务 ID**: DASH-TMPL-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Vue 3 环境

**执行步骤**:
1. 创建 src/views/templates/TemplateList.vue 组件
2. 使用 el-table 显示模板列表
3. 添加版本显示
4. 添加使用统计显示

**输出**:
- src/views/templates/TemplateList.vue 文件

**验证方法**:
```bash
cat src/views/templates/TemplateList.vue
```

**回滚方案**:
```bash
rm src/views/templates/TemplateList.vue
```

**验收标准**:
- [ ] 模板列表显示正常
- [ ] 版本显示正常
- [ ] 使用统计显示正常

---

### 任务 9: 实现模板编辑器
**任务 ID**: DASH-TMPL-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- TemplateList.vue 已创建

**执行步骤**:
1. 创建 src/views/templates/TemplateEditor.vue 组件
2. 使用 Monaco Editor 或 textarea
3. 实现 YAML 语法高亮
4. 实现保存功能

**输出**:
- src/views/templates/TemplateEditor.vue 文件

**验证方法**:
```bash
cat src/views/templates/TemplateEditor.vue
```

**回滚方案**:
```bash
rm src/views/templates/TemplateEditor.vue
```

**验收标准**:
- [ ] 编辑器显示正常
- [ ] 语法高亮正常
- [ ] 保存功能正常

---

### 任务 10: 实现模板预览
**任务 ID**: DASH-TMPL-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- TemplateEditor.vue 已创建

**执行步骤**:
1. 创建 src/views/templates/TemplatePreview.vue 组件
2. 渲染模板结构
3. 显示 Phase 和 Task
4. 显示依赖关系

**输出**:
- src/views/templates/TemplatePreview.vue 文件

**验证方法**:
```bash
cat src/views/templates/TemplatePreview.vue
```

**回滚方案**:
```bash
rm src/views/templates/TemplatePreview.vue
```

**验收标准**:
- [ ] 模板预览正常
- [ ] Phase 显示正常
- [ ] 依赖关系显示正常

---

### 任务 11: 实现模板版本对比
**任务 ID**: DASH-TMPL-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- TemplatePreview.vue 已创建

**执行步骤**:
1. 创建 src/views/templates/VersionCompare.vue 组件
2. 实现版本选择
3. 实现 diff 显示
4. 高亮变更内容

**输出**:
- src/views/templates/VersionCompare.vue 文件

**验证方法**:
```bash
cat src/views/templates/VersionCompare.vue
```

**回滚方案**:
```bash
rm src/views/templates/VersionCompare.vue
```

**验收标准**:
- [ ] 版本选择正常
- [ ] diff 显示正常
- [ ] 高亮正常

---

### 任务 12: 实现模板性能统计
**任务 ID**: DASH-TMPL-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- VersionCompare.vue 已创建
- ECharts 已安装

**执行步骤**:
1. 创建 src/views/templates/TemplateStats.vue 组件
2. 显示成功率统计
3. 显示使用次数
4. 显示平均耗时

**输出**:
- src/views/templates/TemplateStats.vue 文件

**验证方法**:
```bash
cat src/views/templates/TemplateStats.vue
```

**回滚方案**:
```bash
rm src/views/templates/TemplateStats.vue
```

**验收标准**:
- [ ] 统计数据显示正常
- [ ] 图表显示正常

---

### 任务 13: 实现模板匹配测试工具
**任务 ID**: DASH-TMPL-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- TemplateStats.vue 已创建

**执行步骤**:
1. 创建 src/views/templates/TemplateMatcher.vue 组件
2. 添加输入框（用户需求）
3. 显示匹配结果
4. 显示匹配分数

**输出**:
- src/views/templates/TemplateMatcher.vue 文件

**验证方法**:
```bash
cat src/views/templates/TemplateMatcher.vue
```

**回滚方案**:
```bash
rm src/views/templates/TemplateMatcher.vue
```

**验收标准**:
- [ ] 输入框正常
- [ ] 匹配结果正常
- [ ] 分数显示正常

---

### 任务 14: 实现模板管理 API
**任务 ID**: DASH-TMPL-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 前端模板组件已创建

**执行步骤**:
1. 创建 code/backend/api/templates_frontend.py
2. 实现 GET /api/frontend/templates 端点
3. 实现 GET /api/frontend/templates/{id}/versions 端点
4. 实现 POST /api/frontend/templates/{id}/preview 端点

**输出**:
- code/backend/api/templates_frontend.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl http://localhost:8000/api/frontend/templates
```

**回滚方案**:
```bash
rm code/backend/api/templates_frontend.py
```

**验收标准**:
- [ ] 模板列表 API 正常
- [ ] 版本列表 API 正常
- [ ] 预览 API 正常

---

## 阶段四 -3：Agency-Agent 管理（第 1-2 周，06-06 至 06-12）

### 任务 15: 创建 Agent 列表组件
**任务 ID**: DASH-AGENT-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Vue 3 环境

**执行步骤**:
1. 创建 src/views/agents/AgentList.vue 组件
2. 显示 Agent 列表
3. 显示状态（idle/busy）
4. 显示当前任务

**输出**:
- src/views/agents/AgentList.vue 文件

**验证方法**:
```bash
cat src/views/agents/AgentList.vue
```

**回滚方案**:
```bash
rm src/views/agents/AgentList.vue
```

**验收标准**:
- [ ] Agent 列表显示正常
- [ ] 状态显示正常
- [ ] 任务显示正常

---

### 任务 16: 实现 Agent 档案页面
**任务 ID**: DASH-AGENT-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- AgentList.vue 已创建

**执行步骤**:
1. 创建 src/views/agents/AgentProfile.vue 组件
2. 显示 Agent 基本信息
3. 显示技能掌握度
4. 显示经验值

**输出**:
- src/views/agents/AgentProfile.vue 文件

**验证方法**:
```bash
cat src/views/agents/AgentProfile.vue
```

**回滚方案**:
```bash
rm src/views/agents/AgentProfile.vue
```

**验收标准**:
- [ ] 档案信息正常
- [ ] 技能显示正常
- [ ] 经验值显示正常

---

### 任务 17: 实现技能掌握度可视化
**任务 ID**: DASH-AGENT-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- AgentProfile.vue 已创建
- ECharts 已安装

**执行步骤**:
1. 创建 src/components/SkillRadar.vue 组件
2. 使用 ECharts 雷达图
3. 显示各项技能等级
4. 显示成长趋势

**输出**:
- src/components/SkillRadar.vue 文件

**验证方法**:
```bash
cat src/components/SkillRadar.vue
```

**回滚方案**:
```bash
rm src/components/SkillRadar.vue
```

**验收标准**:
- [ ] 雷达图显示正常
- [ ] 技能等级正常
- [ ] 趋势显示正常

---

### 任务 18: 实现团队组建工具
**任务 ID**: DASH-AGENT-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- SkillRadar.vue 已创建

**执行步骤**:
1. 创建 src/views/agents/TeamBuilder.vue 组件
2. 实现 Agent 选择
3. 实现技能匹配度计算
4. 显示团队配置建议

**输出**:
- src/views/agents/TeamBuilder.vue 文件

**验证方法**:
```bash
cat src/views/agents/TeamBuilder.vue
```

**回滚方案**:
```bash
rm src/views/agents/TeamBuilder.vue
```

**验收标准**:
- [ ] Agent 选择正常
- [ ] 匹配度计算正常
- [ ] 建议显示正常

---

### 任务 19: 实现 Agent 分配 API
**任务 ID**: DASH-AGENT-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 前端 Agent 组件已创建

**执行步骤**:
1. 创建 code/backend/api/agents_frontend.py
2. 实现 GET /api/frontend/agents 端点
3. 实现 GET /api/frontend/agents/{id}/profile 端点
4. 实现 POST /api/frontend/agents/assign 端点

**输出**:
- code/backend/api/agents_frontend.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl http://localhost:8000/api/frontend/agents
```

**回滚方案**:
```bash
rm code/backend/api/agents_frontend.py
```

**验收标准**:
- [ ] Agent 列表 API 正常
- [ ] 档案 API 正常
- [ ] 分配 API 正常

---

## 阶段四 -4：优化历史界面（第 2 周，06-13 至 06-19）

### 任务 20: 创建复盘报告列表
**任务 ID**: DASH-OPT-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Vue 3 环境

**执行步骤**:
1. 创建 src/views/optimizations/ReviewList.vue 组件
2. 显示复盘报告列表
3. 添加项目过滤
4. 添加时间过滤

**输出**:
- src/views/optimizations/ReviewList.vue 文件

**验证方法**:
```bash
cat src/views/optimizations/ReviewList.vue
```

**回滚方案**:
```bash
rm src/views/optimizations/ReviewList.vue
```

**验收标准**:
- [ ] 报告列表正常
- [ ] 过滤功能正常

---

### 任务 21: 实现复盘报告详情
**任务 ID**: DASH-OPT-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- ReviewList.vue 已创建

**执行步骤**:
1. 创建 src/views/optimizations/ReviewDetail.vue 组件
2. 显示报告详情
3. 显示问题分析
4. 显示优化建议

**输出**:
- src/views/optimizations/ReviewDetail.vue 文件

**验证方法**:
```bash
cat src/views/optimizations/ReviewDetail.vue
```

**回滚方案**:
```bash
rm src/views/optimizations/ReviewDetail.vue
```

**验收标准**:
- [ ] 报告详情正常
- [ ] 问题分析正常
- [ ] 建议显示正常

---

### 任务 22: 实现模板进化图谱
**任务 ID**: DASH-OPT-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- ReviewDetail.vue 已创建
- ECharts 已安装

**执行步骤**:
1. 创建 src/views/optimizations/TemplateEvolution.vue 组件
2. 使用时间线显示版本历史
3. 显示每次优化内容
4. 显示效果对比

**输出**:
- src/views/optimizations/TemplateEvolution.vue 文件

**验证方法**:
```bash
cat src/views/optimizations/TemplateEvolution.vue
```

**回滚方案**:
```bash
rm src/views/optimizations/TemplateEvolution.vue
```

**验收标准**:
- [ ] 时间线显示正常
- [ ] 优化内容正常
- [ ] 效果对比正常

---

### 任务 23: 实现 Skill 知识库浏览
**任务 ID**: DASH-OPT-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- TemplateEvolution.vue 已创建

**执行步骤**:
1. 创建 src/views/optimizations/SkillLibrary.vue 组件
2. 显示 Skill 列表
3. 添加分类过滤
4. 添加搜索功能

**输出**:
- src/views/optimizations/SkillLibrary.vue 文件

**验证方法**:
```bash
cat src/views/optimizations/SkillLibrary.vue
```

**回滚方案**:
```bash
rm src/views/optimizations/SkillLibrary.vue
```

**验收标准**:
- [ ] Skill 列表正常
- [ ] 分类过滤正常
- [ ] 搜索功能正常

---

### 任务 24: 实现优化效果趋势
**任务 ID**: DASH-OPT-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- SkillLibrary.vue 已创建
- ECharts 已安装

**执行步骤**:
1. 创建 src/views/optimizations/OptimizationTrend.vue 组件
2. 使用折线图显示趋势
3. 显示成功率变化
4. 显示耗时变化

**输出**:
- src/views/optimizations/OptimizationTrend.vue 文件

**验证方法**:
```bash
cat src/views/optimizations/OptimizationTrend.vue
```

**回滚方案**:
```bash
rm src/views/optimizations/OptimizationTrend.vue
```

**验收标准**:
- [ ] 折线图显示正常
- [ ] 趋势数据正常

---

### 任务 25: 实现优化历史 API
**任务 ID**: DASH-OPT-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 前端优化组件已创建

**执行步骤**:
1. 创建 code/backend/api/optimizations_frontend.py
2. 实现 GET /api/frontend/review-reports 端点
3. 实现 GET /api/frontend/optimizations/history 端点
4. 实现 GET /api/frontend/skills 端点

**输出**:
- code/backend/api/optimizations_frontend.py 文件
- 3 个 API 端点

**验证方法**:
```bash
curl http://localhost:8000/api/frontend/review-reports
```

**回滚方案**:
```bash
rm code/backend/api/optimizations_frontend.py
```

**验收标准**:
- [ ] 报告 API 正常
- [ ] 历史 API 正常
- [ ] Skill API 正常

---

## 阶段四 -5：部署与文档（第 2 周，06-13 至 06-19）

### 任务 26: 编写部署文档
**任务 ID**: DEPLOY-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有代码已完成

**执行步骤**:
1. 创建 docs/deployment/README.md
2. 编写环境要求
3. 编写部署步骤
4. 编写配置说明

**输出**:
- docs/deployment/README.md 文件

**验证方法**:
```bash
cat docs/deployment/README.md
```

**回滚方案**:
```bash
rm docs/deployment/README.md
```

**验收标准**:
- [ ] 环境要求清晰
- [ ] 部署步骤完整
- [ ] 配置说明详细

---

### 任务 27: 创建 Docker 生产镜像
**任务 ID**: DEPLOY-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 部署文档已创建

**执行步骤**:
1. 创建 Dockerfile.backend
2. 创建 Dockerfile.frontend
3. 创建 docker-compose.prod.yml
4. 构建镜像测试

**输出**:
- Dockerfile.backend
- Dockerfile.frontend
- docker-compose.prod.yml

**验证方法**:
```bash
docker-compose -f docker-compose.prod.yml build
```

**回滚方案**:
```bash
rm Dockerfile.backend
```

**验收标准**:
- [ ] 镜像构建成功
- [ ] 容器启动正常

---

### 任务 28: 编写用户手册
**任务 ID**: DEPLOY-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 所有功能已完成

**执行步骤**:
1. 创建 docs/user-manual/README.md
2. 编写快速入门
3. 编写功能说明
4. 编写常见问题

**输出**:
- docs/user-manual/README.md 文件

**验证方法**:
```bash
cat docs/user-manual/README.md
```

**回滚方案**:
```bash
rm docs/user-manual/README.md
```

**验收标准**:
- [ ] 快速入门清晰
- [ ] 功能说明完整
- [ ] 常见问题实用

---

### 任务 29: 录制演示视频
**任务 ID**: DEPLOY-001-T04
**预计时长**: 15 分钟
**负责人**: 全员

**输入**:
- 所有功能已完成

**执行步骤**:
1. 准备演示脚本
2. 录制 Dashboard 演示
3. 录制功能演示
4. 剪辑视频

**输出**:
- demos/final-demo.mp4 文件

**验证方法**:
```bash
ls -lh demos/final-demo.mp4
```

**回滚方案**:
```bash
rm demos/final-demo.mp4
```

**验收标准**:
- [ ] 视频完整
- [ ] 画面清晰
- [ ] 时长<10 分钟

---

### 任务 30: 项目终审
**任务 ID**: DEPLOY-001-T05
**预计时长**: 15 分钟
**负责人**: 评审组

**输入**:
- 所有阶段四任务已完成
- 文档已完成
- 演示视频已录制

**执行步骤**:
1. 准备终审材料
2. 演示完整系统
3. 评审组提问
4. 评审组签字

**输出**:
- reviews/final-review-report.md 文件
- 评审组签字

**验证方法**:
```bash
cat reviews/final-review-report.md
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

## 阶段四总结

**总任务数**: 30 个
**总工时**: 7.5 小时（30 × 15 分钟）
**完成率**: 0/30

**关键路径**:
1. 项目管理界面（T01-T07）
2. 模板管理界面（T08-T14）
3. Agency-Agent 管理（T15-T19）
4. 优化历史界面（T20-T25）
5. 部署与文档（T26-T30）

**依赖关系**:
```
项目管理 → 模板管理 → Agency-Agent → 优化历史 → 部署文档
```

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：待执行*
