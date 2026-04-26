# Bug 清单

> **测试轮次**: 端到端测试 TC-E2E-001 ~ TC-E2E-005
> **开始时间**: 2026-04-25 21:13
> **状态**: 进行中

---

## Bug 列表

| Bug ID | 严重程度 | 测试用例 | 问题描述 | 原因分析 | 修复方案 | 状态 | 修复时间 |
|:---|:---:|:---|:---|:---|:---|:---:|:---|
| BUG-001 | P1 | TC-E2E-001 | Agent 创建任务时未传递 input_params | 1. SKILL.md 缺少 input_params 示例<br>2. TaskCreateRequest 缺少 input_params 字段 | 1. 更新 SKILL.md 添加 input_params 示例<br>2. 添加 input_params 到 TaskCreateRequest<br>3. 保存到数据库 | ✅ 已修复 | 21:20 |
| BUG-002 | P0 | TC-E2E-002 | MAF Backend 与 OpenMOSS 字段映射错误 | 1. 未同步创建 OpenMOSS Task<br>2. Authorization header 格式错误<br>3. 缺少 deliverable 字段<br>4. assigned_agent 需要 Agent ID 而非角色名 | 1. 添加 openmoss_task_id 字段<br>2. 同步创建 OpenMOSS Task<br>3. 修复 Authorization header<br>4. 添加 deliverable 字段<br>5. assigned_agent 改为可选 | ✅ 已修复 | 20:45 |
| BUG-003 | P2 | TC-E2E-002 | slowapi 参数错误 | main.py 中全局注册 limiter 但 tasks.py 端点缺少 `request: Request` 参数 | 移除 main.py 中的全局 slowapi 配置，由各路由模块自行管理限流 | ✅ 已修复 | 22:12 |
| BUG-004 | P1 | TC-E2E-005 | Agent 无法取消任务 | 1. SKILL.md 缺少取消任务 API 示例<br>2. Agent 误查找 OpenClaw 内部任务 | 1. 添加取消任务 API 示例<br>2. 明确指示调用 MAF Backend API | ✅ 已修复 | 21:28 |
| BUG-005 | P0 | TC-E2E-007 | 子任务状态未更新 | 1. Backend 缺少完成任务 API<br>2. SKILL.md 缺少调用指引 | 1. 添加 `POST .../complete` 接口<br>2. 更新 SKILL.md 添加示例 | ✅ 已修复 | 22:28 |
| BUG-006 | P1 | TC-E2E-008 | 缺少用户确认提示 | Agent 完成任务后未提示用户确认是否继续 | 在 SKILL.md 中添加完成任务后提示用户确认的指令 | ✅ 已修复 | 22:40 |
| BUG-007 | P0 | TC-E2E-006 | 产出文件未按 Task ID 隔离存放 | 路径硬编码，不同任务文件混杂 | 1. SKILL.md 添加存储规范<br>2. 模板指令更新<br>3. 修复 Docker 挂载路径 | ✅ 已修复 | 23:09 |

---

## 修复记录

### BUG-002 修复记录

**修复时间**: 2026-04-25 20:45

**修复内容**:
1. `app/models/task.py`: 添加 `openmoss_task_id` 字段
2. `app/clients/openmoss_client.py`: 
   - 添加 `create_task()` 方法
   - 修复 Authorization header 为 `Bearer <api_key>`
   - 添加 `deliverable` 字段
   - `assigned_agent` 改为可选参数
3. `app/api/tasks.py`:
   - `create_task` 同步创建 OpenMOSS Task
   - `create_sub_task` 使用 `openmoss_task_id`
4. 数据库迁移: 添加 `openmoss_task_id` 字段

**验证结果**: ✅ 子任务创建成功，数据库记录完整

---

---

## 测试总结

### 第 1 轮测试（2026-04-25 21:15 ~ 21:28）

| TC 编号 | 测试名称 | 结果 | 说明 |
|:---|:---|:---:|:---|
| TC-E2E-001 | 通过 CLI 创建任务 | ✅ PASS | 任务创建成功，input_params 正确保存 |
| TC-E2E-002 | 执行需求分析节点 | ✅ PASS | 子任务创建成功，数据库记录完整 |
| TC-E2E-003 | 查询任务详情 | ✅ PASS | 任务详情和子任务状态正确返回 |
| TC-E2E-004 | 查询任务列表 | ✅ PASS | 任务列表正确返回 |
| TC-E2E-005 | 取消任务 | ✅ PASS | 任务状态更新为 CANCELLED |

**Bug 修复统计**:
- 发现 Bug: 4 个
- 已修复: 4 个
- 待修复: 0 个
- 修复率: 100%

---

## 第 2 轮测试总结

### 测试结果（2026-04-25 21:34 ~ 21:42）

| TC 编号 | 测试名称 | 结果 | 说明 |
|:---|:---|:---:|:---|
| TC-E2E-001 | 通过 CLI 创建任务 | ✅ PASS | 订单管理系统创建成功，input_params 正确保存 |
| TC-E2E-002 | 执行需求分析节点 | ✅ PASS | 子任务创建成功，数据库记录完整 |
| TC-E2E-003 | 查询任务详情 | ✅ PASS | 任务详情和子任务状态正确返回 |
| TC-E2E-004 | 查询任务列表 | ✅ PASS | 任务列表正确返回（15 个任务） |
| TC-E2E-005 | 取消任务 | ✅ PASS | 任务状态更新为 CANCELLED |

### 稳定性验证

- ✅ 所有测试用例在两轮测试中均通过
- ✅ 使用不同的项目名称和技术栈验证了通用性
- ✅ 数据库记录完整且一致

### 累计 Bug 统计

| 状态 | 数量 |
|:---|:---:|
| 已修复 | 4 个 |
| 待修复 | 0 个 |
| 总计 | 4 个 |

---

*文档维护规则：每次发现新 Bug 或修复 Bug 时实时更新此文件。*
