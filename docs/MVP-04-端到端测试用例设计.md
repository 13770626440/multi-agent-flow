# MVP-04 端到端测试用例设计

> **测试阶段**: MVP-04 简单任务验证
> **测试原则**: 严禁 Mock，必须通过 OpenClaw CLI 模拟用户与 Agent 真实对话；悲观验收，有瑕疵即不通过。
> **执行时间**: 2026-04-26
> **执行人**: 测试组

---

## 测试环境确认

| 检查项 | 状态 | 说明 |
|--------|------|------|
| Docker 容器 | ✅ | 5 个容器全部 Up (healthy) |
| Backend API | ✅ | `http://127.0.0.1:8000/api/v1/health` 返回 ok，数据库 connected |
| OpenMOSS | ✅ | `http://127.0.0.1:6565/api/health` 返回 ok |
| OpenClaw | ✅ | Port 18789 可访问 |
| Skill 挂载 | ⏳ | 待验证 `multi-agent-flow-manager` 是否正确加载 |
| 模板加载 | ⏳ | 待验证 `simple-dev-flow` 模板是否被 Redis 缓存 |

---

## TC-MVP04-01: 固定任务模板创建与需求分析

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证通过 Agent 对话创建基于 `simple-dev-flow` 模板的任务，并完成第一个固定节点（需求分析）。 |
| **完整故事线** | 用户发送创建任务指令 → Agent 识别意图并提取参数 → Agent 调用 Backend API 创建任务 → Backend 加载模板并创建第一个子任务（需求分析） → Agent 执行需求分析并输出 PRD 文档 → Agent 调用完成 API 更新状态。 |
| **输入 (模拟人)** | `"帮我创建一个任务，使用 simple-dev-flow 模板，项目名称是'用户管理系统'，技术栈是 FastAPI + Vue3。"` |
| **预期输出 (Agent)** | 1. 回复："✅ 任务创建成功！任务 ID: [UUID]"<br>2. 执行需求分析节点，输出 PRD 文档<br>3. 回复："✅ **需求分析** 已完成。产出文件已保存。是否继续执行下一个节点（**开发任务分解**）？" |
| **数据与日志依据** | 1. **Agent 侧日志**：显示 `POST /api/v1/tasks/` 调用成功，提取到 task_id<br>2. **Backend 日志**：`POST /api/v1/tasks/` 返回 200，模板加载成功，创建子任务<br>3. **DB 验证**：`task_instances` 表存在记录，`template_id='simple-dev-flow'`；`sub_task_records` 表存在需求分析子任务<br>4. **文件验证**：`/workspace/{task_id}/req-analysis/prd.md` 文件存在，内容包含至少 3 个核心功能<br>5. **OpenMOSS 日志**：存在子任务创建记录 |
| **悲观验收结论** | **FAIL 条件**：<br>1. Agent 未调用 Backend API 创建任务<br>2. 模板未正确加载或解析失败<br>3. PRD 文档未生成或内容不完整（少于 3 个核心功能）<br>4. Agent 未调用完成 API 更新子任务状态<br>5. Agent 回复未包含 Task ID 或未询问是否继续 |

---

## TC-MVP04-02: 动态任务分解验证

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证动态任务分解节点（dev-breakdown）能正确通过 OpenMOSS 调度 Agent 完成分解，输出合法 JSON。 |
| **完整故事线** | 用户确认继续 → Agent 调用创建子任务 API 创建动态分解节点 → OpenMOSS 调度 tech-lead Agent → Agent 读取 PRD 文档并分解任务 → 输出 JSON 数组 → Agent 调用完成 API → 询问用户确认分解结果。 |
| **输入 (模拟人)** | `"继续"`（在需求分析完成后） |
| **预期输出 (Agent)** | 1. 回复："✅ **开发任务分解** 已完成。分解出 [N] 个子任务。请确认分解结果是否合理？"<br>2. 输出 JSON 格式的子任务列表，每个子任务包含 name、role、instruction、dependencies |
| **数据与日志依据** | 1. **Backend 日志**：`POST /api/v1/tasks/{task_id}/sub-tasks` 创建动态分解子任务成功<br>2. **OpenMOSS 日志**：子任务状态流转 assigned → in_progress → done<br>3. **DB 验证**：`sub_task_records` 表中 dev-breakdown 子任务 `status='done'`，`decomposition_output` 包含合法 JSON<br>4. **文件验证**：`/workspace/{task_id}/dev-breakdown/sub-tasks.json` 存在且格式正确<br>5. **JSON 校验**：输出为数组，每个元素包含 name(string)、role(enum)、instruction(string)、dependencies(array) |
| **悲观验收结论** | **FAIL 条件**：<br>1. 动态分解未通过 OpenMOSS 调度，而是 Backend 直接调用 LLM<br>2. 输出 JSON 格式错误或 Schema 校验失败<br>3. 缺少必填字段（name/role/instruction）<br>4. 存在循环依赖<br>5. Agent 未询问用户确认分解结果 |

---

## TC-MVP04-03: 完整流程测试（固定→动态→评审→部署）

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证完整任务生命周期：固定任务 → 动态分解 → 评审 → 部署，全链路通畅。 |
| **完整故事线** | 用户依次确认每个节点继续执行 → Agent 按模板顺序执行 4 个节点 → 每个节点完成后调用完成 API → 最终输出部署日志。 |
| **输入 (模拟人)** | 依次回复 `"继续"` 共 4 次（需求分析→任务分解→代码审查→部署上线） |
| **预期输出 (Agent)** | 每个节点完成后回复标准格式，最终回复："✅ **部署上线** 已完成。服务已部署，健康检查通过。" |
| **数据与日志依据** | 1. **DB 验证**：4 个子任务全部 `status='done'`，按依赖顺序完成<br>2. **文件验证**：<br>   - `/workspace/{task_id}/req-analysis/prd.md`<br>   - `/workspace/{task_id}/dev-breakdown/sub-tasks.json`<br>   - `/workspace/{task_id}/code-review/review-report.md`<br>   - `/workspace/{task_id}/deploy/deploy-log.md`<br>3. **Backend 日志**：每个子任务创建和完成 API 调用均有 200 响应<br>4. **OpenMOSS 日志**：4 个子任务状态完整流转 |
| **悲观验收结论** | **FAIL 条件**：<br>1. 任何节点执行失败或跳过<br>2. 依赖关系未遵守（如部署在审查前执行）<br>3. 任何产出文件缺失<br>4. Agent 未调用完成 API 导致状态未更新<br>5. 响应时间单个节点 > 60s |

---

## TC-MVP04-04: OpenMOSS Dashboard 验证

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证 OpenMOSS Dashboard 能正确展示任务状态、子任务进度、Agent 状态。 |
| **完整故事线** | 在 TC-MVP04-03 执行过程中，访问 OpenMOSS Dashboard → 查看任务列表 → 查看子任务状态 → 验证数据与 Backend DB 一致。 |
| **输入 (模拟人)** | 浏览器访问 `http://127.0.0.1:6565` 或调用 Dashboard API |
| **预期输出** | 1. Dashboard 显示当前任务列表<br>2. 子任务状态与 Backend DB 一致<br>3. Agent 状态显示正确（planner/executor/reviewer） |
| **数据与日志依据** | 1. **Dashboard 截图**：保存任务执行过程中的 Dashboard 状态截图<br>2. **API 验证**：`GET /api/sub-tasks?task_id={task_id}` 返回子任务列表，状态与 DB 一致<br>3. **Agent 列表**：`GET /api/agents` 返回已注册的 4 个 Agent |
| **悲观验收结论** | **FAIL 条件**：<br>1. Dashboard 无法访问或报错<br>2. 子任务状态与 Backend DB 不一致<br>3. Agent 未正确注册或状态异常 |

---

## 测试执行记录模板

### TC-MVP04-01 执行记录

| 项目 | 内容 |
|------|------|
| **执行时间** | 2026-04-26 HH:MM |
| **执行人** | 测试组 |
| **输入** | （记录实际输入） |
| **Agent 回复** | （记录完整回复） |
| **Backend 日志** | （记录关键日志） |
| **数据库验证** | （记录查询结果） |
| **文件验证** | （记录文件存在性和内容摘要） |
| **测试结论** | ✅ PASS / ❌ FAIL |

### 失败原因分析（如 FAIL）

1. ...
2. ...

### 修复建议

1. ...
2. ...

---

*文档维护规则：测试执行后，必须将真实数据和日志摘要填入执行记录表。*
