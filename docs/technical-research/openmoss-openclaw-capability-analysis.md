# OpenMOSS & OpenClaw 能力边界调研与技术验证报告

> 调研日期：2026-04-21 23:02
> 调研目的：验证OpenMOSS和OpenClaw Lobster的实际能力边界，与我们构想的架构进行对比分析

---

## 一、OpenMOSS 能力边界

### 1.1 基本信息

| 项目 | 内容 |
|------|------|
| **项目地址** | https://github.com/uluckyXH/OpenMOSS |
| **最新版本** | v1.1.3（2026-04-02） |
| **技术栈** | FastAPI + Vue 3 + SQLite/PostgreSQL |
| **默认端口** | 6565 |
| **开源协议** | MIT |

### 1.2 核心定位

**OpenMOSS是一个面向OpenClaw的多Agent协作调度中间件**，不直接运行AI模型，而是通过组织架构化管理AI工作流。

### 1.3 实际API能力

#### 1.3.1 已确认的API端点

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| **健康检查** | `/api/health` | GET | 服务健康检查 |
| **Agent注册** | `/api/agents/register` | POST | Agent注册，需Header携带`X-Registration-Token` |
| **Agent信息** | `/agents/me` | GET | Agent查询自身信息 |
| **Agent技能** | `/agents/me/skill` | GET | 获取当前角色对应的SKILL.md |
| **通知配置** | `/config/notification` | GET | Agent读取通知配置 |
| **任务管理** | `/api/tasks/*` | CRUD | 任务CRUD操作 |
| **子任务管理** | `/api/sub_tasks/*` | CRUD | 子任务生命周期管理（认领、状态更新、提交审查） |
| **审查记录** | `/api/review_records/*` | POST | 审查提交接口（质量评分、通过/驳回） |
| **绩效积分** | `/api/scores/*` | GET | 绩效积分计算与排行榜查询 |
| **活动日志** | `/api/logs/*` | GET | 活动日志记录 |
| **活动流** | `/api/feed/*` | GET | 实时活动流推送 |
| **全局规则** | `/api/rules/*` | GET | 全局规则查询与版本更新提示 |
| **管理端-Agent** | `/admin/agents/*` | GET | 管理端Agent列表查询、工作量统计 |
| **管理端-任务** | `/admin/tasks/*` | GET/PUT | 管理端任务管理 |
| **管理端-审查** | `/admin/reviews/*` | GET | 管理端审查记录查询 |
| **管理端-配置** | `/admin/config/*` | GET/PUT | 管理端配置管理 |
| **管理端-仪表板** | `/admin/dashboard/*` | GET | 管理端仪表板数据 |
| **初始化向导** | `/api/setup/*` | POST | 密码设置、项目配置、令牌生成 |

#### 1.3.2 认证机制（双层Header认证）

| 角色 | 认证方式 | Header |
|------|---------|--------|
| Agent | 内部API Key | `X-Agent-Key: <api_key>`（`om_`开头） |
| 管理员 | Admin Token | `X-Admin-Token: <token>`（通过`/login`获取） |
| 注册 | 注册令牌 | `X-Registration-Token: <token>`（config.yaml中定义） |

### 1.4 任务调度机制

#### 1.4.1 调度模式：Cron定时唤醒 + 队列原子流转

```
Agent被cron唤醒 → 调用API拉取当前队列状态 → 按角色执行对应操作 → 将结果回写OpenMOSS → 进入休眠
```

#### 1.4.2 角色调度频率（可配置）

| 角色 | 默认频率 | 职责 |
|------|---------|------|
| planner（规划者） | 每30分钟 | 检查新任务并拆解 |
| executor（执行者） | 每15分钟 | 认领并执行子任务 |
| reviewer（审查者） | 每20分钟 | 审查交付物 |
| patrol（巡查者） | 每10分钟 | 巡检系统阻塞与异常 |

#### 1.4.3 任务流转闭环

```
1. Planner接收主任务 → 拆分子任务并定义验收标准
2. Executor从队列认领 → 执行并交付产物
3. Reviewer审查 → 通过则标记完成，驳回则打回重做
4. Patrol持续监控 → 发现超时/死循环自动标记blocked并告警
```

#### 1.4.4 任务结构（三级层级）

```
Task（任务） → Module（模块） → Sub-Task（子任务）
```

#### 1.4.5 状态流转

```
pending → assigned → in_progress → review → done
                          ↓                ↓
                      rework ←──────── 审查驳回
                          ↓
                      blocked（巡查发现阻塞）
```

### 1.5 Agent管理能力

| 能力 | 支持情况 | 说明 |
|------|---------|------|
| Agent注册 | ✅ 支持 | WebUI可视化注册或API注册 |
| 独立身份 | ✅ 支持 | 每个Agent有唯一API Key（`om_`开头） |
| 技能绑定 | ✅ 支持 | 热更新SKILL.md，下次唤醒自动生效 |
| 状态监控 | ✅ 支持 | WebUI展示最后活跃时间、API调用流水、工作量 |
| 绩效系统 | ✅ 支持 | 内置积分系统，Reviewer评分计入绩效排行 |
| 独立模型配置 | ✅ 支持 | 每个Agent对应独立OpenClaw实例，需单独配置LLM API Key |
| 异常干预 | ✅ 支持 | Patrol自动识别死循环/阻塞，通知管理员 |

### 1.6 关键限制

| 限制 | 说明 | 影响 |
|------|------|------|
| **非实时API调用** | Agent通过cron定时唤醒，非实时响应 | 无法实现即时任务派发和实时状态同步 |
| **任务结构固定** | Task→Module→Sub-Task三级结构 | 不支持我们设计的灵活任务层级和动态分解 |
| **状态机固定** | pending→assigned→in_progress→review→done | 不支持我们设计的conditional_approved等状态 |
| **无并行控制** | 任务队列具备原子性保护，但无并行组概念 | 不支持我们设计的parallel_group并行执行 |
| **无模板系统** | 无任务模板定义和实例化机制 | 需要我们自建模板系统 |
| **无分解策略** | 无任务分解策略框架 | 需要我们自建分解策略 |
| **无Trace追踪** | 无全链路追踪ID | 需要我们自建可观测性系统 |

---

## 二、OpenClaw Lobster 能力边界

### 2.1 基本信息

| 项目 | 内容 |
|------|------|
| **项目地址** | https://github.com/openclaw/openclaw |
| **最新版本** | v2026.4.15（2026-04-16） |
| **代号** | The Lobster（龙虾） |
| **技术栈** | Node.js + TypeScript |
| **默认端口** | 18789（Gateway） |
| **开源协议** | MIT |

### 2.2 核心定位

**OpenClaw是一个自托管的AI Agent网关**，专为开发者与高级用户设计，支持20+聊天平台接入，提供Agent运行时环境。

### 2.3 实际API能力

#### 2.3.1 Gateway REST API

**Base URL**: `http://127.0.0.1:18789/api/v1`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/status` | 详细系统状态 |
| POST | `/message` | 向Agent发送消息（支持同步/异步/SSE流式） |
| GET | `/conversations` | 列出对话（支持分页与筛选） |
| GET | `/conversations/:id` | 获取特定对话的完整消息历史 |
| DELETE | `/conversations/:id` | 删除特定对话及其关联记忆 |
| GET | `/memory/stats` | 获取记忆系统统计信息 |
| POST | `/memory/search` | 搜索记忆内容 |
| DELETE | `/memory/prune` | 按条件清理记忆 |
| GET | `/skills` | 列出已安装技能 |
| POST | `/skills/install` | 安装新技能 |
| DELETE | `/skills/:name` | 移除指定技能 |
| GET | `/channels` | 列出已配置的通信平台连接状态 |
| GET | `/channels/:type/status` | 获取特定平台状态 |
| GET | `/config` | 获取当前配置（敏感字段已脱敏） |
| PUT | `/config` | 部分更新配置 |
| GET | `/logs` | 获取系统日志（支持按级别/组件/时间筛选） |

#### 2.3.2 工具调用HTTP API

**端点**: `POST /tools/invoke`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tool` | 字符串 | ✅ | 要调用的工具名称 |
| `action` | 字符串 | ❌ | 工具特定的动作 |
| `args` | 对象 | ❌ | 工具参数 |
| `sessionKey` | 字符串 | ❌ | 目标会话键（省略或"main"使用主会话） |

**认证**: `Authorization: Bearer <gateway_token>`

**安全限制**: 默认禁止高危工具（exec, shell, fs_write, fs_delete, gateway, cron, sessions_spawn等）

### 2.4 Agent生命周期管理

#### 2.4.1 会话级管理（非Agent级）

OpenClaw的"Agent"概念是**会话级**的，而非独立的Agent实例：

| 能力 | 支持情况 | 说明 |
|------|---------|------|
| 会话隔离 | ✅ 支持 | 为每个消息发送者自动创建并维护独立会话 |
| 会话持久化 | ✅ 支持 | 树状结构JSONL文件，SessionManager管理 |
| 上下文压缩 | ✅ 支持 | 自动压缩，支持手动压缩 |
| 事件订阅 | ✅ 支持 | agent_start/agent_end, turn_start/turn_end, tool_execution_start/end等 |
| 错误处理 | ✅ 支持 | 上下文溢出、压缩失败、认证失败、限流等精准分类 |
| 模型故障转移 | ✅ 支持 | 配置回退模型，FailoverError触发切换 |

#### 2.4.2 不支持的能力

| 能力 | 支持情况 | 说明 |
|------|---------|------|
| Agent实例管理 | ❌ 不支持 | 无独立的Agent创建/启动/暂停/终止API |
| Agent生命周期 | ❌ 不支持 | 无Agent级别的状态机 |
| Agent资源管理 | ❌ 不支持 | 无Agent级别的CPU/内存/工具权限管理 |
| Agent编排 | ❌ 不支持 | 无多Agent编排和调度能力 |

### 2.5 工具调用机制

#### 2.5.1 三层协同架构

```
工具(Tools) → 技能(Skills) → 插件(Plugins)
```

| 层级 | 说明 |
|------|------|
| **工具** | LLM可调用的类型化函数（exec, browser, web_search等） |
| **技能** | SKILL.md形式注入系统提示词，提供上下文和指导 |
| **插件** | 打包并注册工具、Skills、渠道、模型提供商等能力 |

#### 2.5.2 核心执行工具

| 工具 | 说明 |
|------|------|
| exec/process | 运行Shell命令及管理后台进程 |
| code_execution | 沙箱隔离的远程Python分析环境 |
| read/write/edit | 安全的工作区I/O |
| apply_patch | 多段文件补丁 |
| message | 跨所有消息渠道发送内容 |
| sessions_* | 会话管理、状态查看与多智能体调度 |
| gateway | 配置树查询、配置快照、热更新、自更新/重启 |

### 2.6 关键限制

| 限制 | 说明 | 影响 |
|------|------|------|
| **非Agent生命周期管理系统** | OpenClaw是聊天网关+Agent运行时，非专用Agent管理系统 | 无法实现我们构想的Agent构建/启动/暂停/终止 |
| **无Agent编排能力** | 无多Agent编排和调度 | 需要OpenMOSS或其他系统补充 |
| **工具调用受限** | 默认禁止高危工具通过HTTP调用 | 需要调整安全策略 |
| **会话级隔离** | Agent概念是会话级，非独立实例 | 与我们的Agent实例构想有差异 |

---

## 三、与我们构想的差异分析

### 3.1 差异对比表

| 维度 | 我们的构想 | OpenMOSS实际能力 | OpenClaw实际能力 | 差异程度 | 应对策略 |
|------|-----------|-----------------|-----------------|---------|---------|
| **任务调度** | 实时API调用，即时派发 | Cron定时唤醒（10-30分钟间隔） | 不支持任务调度 | 🔴 重大 | Backend直接管理任务状态，通过OpenMOSS API或OpenClaw API触发执行 |
| **任务模板** | YAML模板定义+实例化 | 无模板系统 | 无模板系统 | 🔴 重大 | Backend自建模板系统 |
| **任务分解** | 策略化分解，记录分解依据 | 无分解策略框架 | 无分解能力 | 🔴 重大 | Backend自建分解策略 |
| **并行执行** | parallel_group并行组 | 无并行组概念 | 不支持 | 🔴 重大 | Backend自建并行调度器 |
| **验收评审** | 评审组评审，支持部分通过 | 支持审查（reviewer角色） | 不支持 | 🟡 中等 | 复用OpenMOSS审查机制，或自建评审系统 |
| **Agent构建** | OpenMOSS构建Agent实例 | 不支持Agent构建 | 不支持Agent实例管理 | 🔴 重大 | Backend直接调用OpenClaw API创建会话 |
| **Agent生命周期** | 启动/暂停/恢复/终止 | 不支持 | 不支持Agent级别 | 🔴 重大 | 通过OpenClaw会话管理模拟 |
| **状态同步** | 实时同步任务状态 | 定时回写（cron间隔） | 事件订阅支持 | 🟡 中等 | Backend轮询OpenMOSS API或订阅OpenClaw事件 |
| **可观测性** | Trace ID全链路追踪 | 无 | 事件订阅支持 | 🟡 中等 | Backend自建追踪系统 |

### 3.2 核心差异总结

#### 差异1：任务调度模式

**我们的构想**：Backend通过API实时派发任务到OpenMOSS，OpenMOSS即时调度Agent执行。

**实际情况**：OpenMOSS采用Cron定时唤醒模式，Agent每10-30分钟醒来检查任务队列，执行后回写结果。

**影响**：无法实现实时任务派发和状态同步，任务执行延迟取决于cron间隔。

#### 差异2：Agent管理粒度

**我们的构想**：OpenMOSS负责Agent实例的构建、启动、暂停、终止等生命周期管理。

**实际情况**：OpenMOSS只管理Agent注册和配置，实际Agent是独立的OpenClaw实例。OpenClaw提供会话级管理，无独立Agent实例概念。

**影响**：需要重新设计Agent管理方式，可能由Backend直接管理OpenClaw会话。

#### 差异3：任务系统灵活性

**我们的构想**：灵活的任务层级、动态分解、并行执行、模板继承等。

**实际情况**：OpenMOSS采用固定的Task→Module→Sub-Task三级结构，无模板、无分解策略、无并行组。

**影响**：Backend需要自建完整的任务管理系统，OpenMOSS仅作为Agent协作层使用。

---

## 四、重新设计的模块边界

### 4.1 架构调整建议

基于调研结果，建议调整架构如下：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Backend（自研）                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  模板管理系统  │  │  任务管理系统  │  │  评审管理系统  │  │  可观测性系统    │ │
│  │ - YAML模板   │  │ - 任务CRUD   │  │ - 验收标准   │  │ - Trace ID      │ │
│  │ - 模板继承   │  │ - 任务分解   │  │ - 评审流程   │  │ - 执行链路追踪  │ │
│  │ - 实例化     │  │ - 并行调度   │  │ - 部分通过   │  │ - 性能分析      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        OpenMOSS适配层                                   │ │
│  │ - 任务派发（调用OpenMOSS API）                                          │ │
│  │ - 状态同步（轮询OpenMOSS API）                                          │ │
│  │ - Agent注册管理                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        OpenClaw适配层                                   │ │
│  │ - 会话管理（POST /message）                                             │ │
│  │ - 工具调用（POST /tools/invoke）                                        │ │
│  │ - 事件订阅（SSE流式）                                                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│      OpenMOSS       │              │      OpenClaw       │
│  - Agent协作调度     │              │  - Agent运行时      │
│  - 任务队列管理      │              │  - 工具执行         │
│  - 审查流程          │              │  - 会话管理         │
│  - 绩效系统          │              │  - 记忆系统         │
└─────────────────────┘              └─────────────────────┘
```

### 4.2 职责重新划分

| 模块 | 职责 | 技术实现 |
|------|------|---------|
| **Backend-模板管理** | 任务模板定义、继承、实例化 | FastAPI + SQLAlchemy + YAML解析 |
| **Backend-任务管理** | 任务CRUD、分解、并行调度 | FastAPI + asyncio + 自定义调度器 |
| **Backend-评审管理** | 验收标准、评审流程、部分通过 | FastAPI + 自定义评审引擎 |
| **Backend-可观测性** | Trace ID、链路追踪、性能分析 | OpenTelemetry + 自定义追踪 |
| **Backend-OpenMOSS适配** | 任务派发、状态同步、Agent注册 | HTTP Client + 轮询机制 |
| **Backend-OpenClaw适配** | 会话管理、工具调用、事件订阅 | HTTP Client + SSE流式订阅 |
| **OpenMOSS** | Agent协作调度、任务队列、审查流程 | 现有OpenMOSS系统 |
| **OpenClaw** | Agent运行时、工具执行、会话管理 | 现有OpenClaw系统 |

---

## 五、调用推演

### 5.1 场景：基于模板创建任务并执行

```
1. 用户请求创建任务
   POST /api/tasks/instantiate
   Body: {
     "template_id": "project-dev-workflow-v1",
     "parameters": {"project_name": "AI教育平台"}
   }

2. Backend模板引擎处理
   - 加载模板YAML
   - 替换参数
   - 创建任务实例（Task记录）
   - 生成Trace ID

3. Backend任务分解
   - 根据模板定义分解子任务
   - 记录分解依据
   - 设置并行组
   - 设置依赖关系

4. Backend派发任务到OpenMOSS
   POST http://openmoss:6565/api/tasks
   Headers: {X-Admin-Token: <token>}
   Body: {
     "name": "需求收集",
     "description": "...",
     "acceptance_criteria": ["..."],
     "assigned_agent": "planner"
   }

5. OpenMOSS接收任务
   - 创建任务记录
   - 加入任务队列
   - 等待planner cron唤醒

6. Planner Agent被cron唤醒（每30分钟）
   - 调用GET /api/tasks?status=pending
   - 认领任务
   - 执行任务（调用OpenClaw）

7. Planner调用OpenClaw执行
   POST http://openclaw:18789/api/v1/message
   Headers: {Authorization: Bearer <token>}
   Body: {
     "channel": "api",
     "message": "请收集AI教育平台的需求...",
     "conversation_id": "conv_planner_001",
     "wait_for_response": true,
     "timeout_ms": 300000
   }

8. OpenClaw执行任务
   - LLM处理消息
   - 调用工具（web_search, file_write等）
   - 返回执行结果

9. Planner回写结果到OpenMOSS
   PUT /api/sub_tasks/{id}/status
   Body: {"status": "review", "output": "..."}

10. Backend轮询OpenMOSS状态
    GET /api/tasks/{id}
    - 检查任务状态是否变更为review

11. Reviewer Agent被cron唤醒（每20分钟）
    - 调用GET /api/sub_tasks?status=review
    - 审查交付物
    - 提交审查结果

12. Backend同步最终状态
    - 更新本地任务状态
    - 记录评审结果
    - 触发后续任务
```

### 5.2 场景：动态任务分解

```
1. 用户提交动态任务
   POST /api/tasks
   Body: {
     "name": "修复登录Bug",
     "type": "dynamic",
     "input_data": {"bug_report": "..."}
   }

2. Backend调用分解策略
   decomposition_strategy = BugFixDecomposition()
   subtasks = decomposition_strategy.decompose(task, context)

3. 分解策略分析Bug报告
   - 提取根因
   - 为每个根因创建子任务
   - 记录分解依据

4. Backend创建子任务
   for subtask in subtasks:
     POST /api/tasks
     Body: {
       "name": subtask.name,
       "parent_task_id": task.id,
       "decomposition_basis": subtask.basis,
       "acceptance_criteria": subtask.criteria
     }

5. 后续流程同场景1
```

### 5.3 场景：并行任务执行

```
1. Backend检查并行组
   parallel_group = "design"
   tasks = get_tasks_by_parallel_group(parallel_group)

2. Backend检查依赖
   for task in tasks:
     if not check_dependencies_completed(task.dependencies):
       skip task

3. Backend派发并行任务到OpenMOSS
   for task in ready_tasks:
     POST /api/tasks (OpenMOSS)
     - 异步派发，不等待响应

4. OpenMOSS接收任务
   - 加入任务队列
   - 等待对应Agent cron唤醒

5. 多个Agent并行执行
   - executor1认领任务A
   - executor2认领任务B
   - executor3认领任务C
   - 并行调用OpenClaw

6. Backend轮询同步状态
   - 定期检查所有并行任务状态
   - 当全部完成且通过评审，触发后续任务
```

---

## 六、技术验证结论

### 6.1 验证结果

| 验证项 | 验证方式 | 结果 | 说明 |
|--------|---------|------|------|
| OpenMOSS API可用性 | 文档调研 | ✅ 可用 | FastAPI提供完整REST API |
| OpenMOSS任务调度 | 文档调研 | ⚠️ 有限 | Cron定时唤醒，非实时API调用 |
| OpenMOSS Agent管理 | 文档调研 | ⚠️ 有限 | 仅注册和配置，无生命周期管理 |
| OpenClaw API可用性 | 文档调研 | ✅ 可用 | Gateway REST API + 工具调用API |
| OpenClaw Agent管理 | 文档调研 | ❌ 不支持 | 会话级管理，无Agent实例概念 |
| OpenClaw工具调用 | 文档调研 | ✅ 可用 | POST /tools/invoke |
| OpenClaw事件订阅 | 文档调研 | ✅ 可用 | SSE流式事件订阅 |

### 6.2 风险与建议

| 风险 | 严重程度 | 建议 |
|------|---------|------|
| OpenMOSS非实时调度 | 高 | Backend直接管理任务状态，OpenMOSS仅作为Agent协作层 |
| OpenClaw无Agent实例管理 | 高 | 通过会话管理模拟Agent实例，或考虑其他Agent框架 |
| 任务系统需自建 | 高 | Backend自建完整任务管理系统 |
| Cron延迟影响体验 | 中 | 可调整cron间隔，或通过API主动触发唤醒 |
| 工具调用安全限制 | 中 | 调整OpenClaw安全策略，允许必要工具 |

### 6.3 下一步行动

1. **确认架构调整**：根据本调研结果，重新设计Backend/OpenMOSS/OpenClaw职责边界
2. **技术验证POC**：搭建最小验证环境，实际调用OpenMOSS和OpenClaw API验证关键流程
3. **完善数据模型**：根据实际能力调整Task、Template、Review等数据模型
4. **编写适配层代码**：开发OpenMOSSClient和OpenClawClient封装

---

*报告完成时间：2026-04-21 23:30*
*下次更新：技术验证POC完成后*
