# Backend / OpenMOSS / OpenClaw 三组件边界与流程推演

> 推演日期：2026-04-21 23:24
> 推演目的：基于技术验证结果，详细定义三个组件的职责边界和完整调用流程

---

## 一、组件职责边界

### 1.1 总体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Backend（自研 - 大脑）                             │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  模板管理系统  │  │  任务管理系统  │  │  评审管理系统  │  │  可观测性系统    │ │
│  │  - YAML模板  │  │  - 任务CRUD  │  │  - 验收标准  │  │  - Trace ID     │ │
│  │  - 模板继承  │  │  - 任务分解  │  │  - 评审流程  │  │  - 链路追踪     │ │
│  │  - 实例化    │  │  - 并行调度  │  │  - 部分通过  │  │  - 性能分析     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        任务派发引擎                                    │  │
│  │                                                                       │  │
│  │  1. 主动派发：调用OpenClaw API直接发送任务指令（实时）                  │  │
│  │  2. 定时补偿：定期检查OpenMOSS状态，发现超时重新派发（每5分钟）         │  │
│  │  3. 状态同步：保持Backend和OpenMOSS的状态一致                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        适配层                                          │  │
│  │                                                                       │  │
│  │  OpenMOSSClient: 任务队列管理、Agent注册、审查流程                     │  │
│  │  OpenClawClient: 消息发送、工具调用、会话管理、事件订阅                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
         │                                      │
         │ 主动派发（实时）                      │ 定时补偿（每5分钟）
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│      OpenClaw       │              │      OpenMOSS       │
│  （执行层 - 手脚）   │              │  （协作层 - 中枢）   │
│                     │              │                     │
│  - Agent运行时      │              │  - 任务队列持久化    │
│  - 工具执行         │              │  - Agent注册管理     │
│  - 会话管理         │              │  - 审查流程          │
│  - 记忆系统         │              │  - 绩效系统          │
│  - 技能系统         │              │  - 活动日志          │
└─────────────────────┘              └─────────────────────┘
```

### 1.2 职责详细划分

| 功能模块 | Backend | OpenMOSS | OpenClaw | 说明 |
|---------|---------|----------|----------|------|
| **任务模板定义** | ✅ 主责 | ❌ | ❌ | YAML模板、继承、实例化 |
| **任务分解** | ✅ 主责 | ❌ | ❌ | 策略化分解、记录依据 |
| **任务派发** | ✅ 主责 | ⚠️ 辅助 | ⚠️ 辅助 | Backend主动派发，OpenMOSS记录队列 |
| **任务执行** | ❌ | ❌ | ✅ 主责 | Agent运行时、工具调用 |
| **会话管理** | ❌ | ❌ | ✅ 主责 | 对话ID、上下文、记忆 |
| **任务队列** | ⚠️ 缓存 | ✅ 主责 | ❌ | OpenMOSS持久化任务状态 |
| **Agent注册** | ⚠️ 触发 | ✅ 主责 | ❌ | OpenMOSS管理Agent身份 |
| **审查流程** | ⚠️ 触发 | ✅ 主责 | ❌ | OpenMOSS管理审查队列 |
| **评审管理** | ✅ 主责 | ❌ | ❌ | Backend管理验收标准 |
| **状态同步** | ✅ 主责 | ⚠️ 提供API | ❌ | Backend轮询OpenMOSS |
| **可观测性** | ✅ 主责 | ❌ | ❌ | Trace ID、链路追踪 |

### 1.3 数据归属

| 数据类型 | 存储位置 | 说明 |
|---------|---------|------|
| 任务模板 | Backend数据库 | YAML模板、版本管理 |
| 任务实例 | Backend数据库 + OpenMOSS数据库 | Backend为主，OpenMOSS为队列 |
| 子任务状态 | OpenMOSS数据库 | 任务队列持久化 |
| Agent身份 | OpenMOSS数据库 | Agent注册信息、API Key |
| 会话上下文 | OpenClaw文件系统 | 对话历史、记忆 |
| 执行结果 | Backend数据库 | 任务输出、评审结果 |
| 评审记录 | Backend数据库 | 验收标准、评审意见 |
| Trace日志 | Backend数据库 | 全链路追踪 |

---

## 二、核心场景流程推演

### 场景1：基于模板创建任务并主动派发

#### 2.1.1 流程图

```
用户                Backend                OpenMOSS              OpenClaw
 │                    │                      │                     │
 │  1.创建任务         │                      │                     │
 │───────────────────→│                      │                     │
 │  {template_id,     │                      │                     │
 │   parameters}      │                      │                     │
 │                    │                      │                     │
 │                    │  2.加载模板           │                     │
 │                    │  替换参数             │                     │
 │                    │  创建任务实例          │                     │
 │                    │  生成Trace ID         │                     │
 │                    │                      │                     │
 │                    │  3.任务分解           │                     │
 │                    │  (策略化分解)          │                     │
 │                    │                      │                     │
 │                    │  4.创建子任务          │                     │
 │                    │─────────────────────→│                     │
 │                    │  POST /sub-tasks      │                     │
 │                    │  {task_id, name,      │                     │
 │                    │   assigned_agent,     │                     │
 │                    │   acceptance}         │                     │
 │                    │                      │                     │
 │                    │  5.主动派发任务        │                     │
 │                    │────────────────────────────────────────────→│
 │                    │  POST /api/v1/message │                     │
 │                    │  {channel:"api",      │                     │
 │                    │   message:"请执行...", │                     │
 │                    │   conversation_id,    │                     │
 │                    │   wait_for_response:  │                     │
 │                    │   true, timeout_ms}   │                     │
 │                    │                      │                     │
 │                    │                      │                     │  6.执行任务
 │                    │                      │                     │  (LLM+工具)
 │                    │                      │                     │
 │                    │  7.返回执行结果        │                     │
 │                    │←────────────────────────────────────────────│
 │                    │  {content:"...",      │                     │
 │                    │   conversation_id}    │                     │
 │                    │                      │                     │
 │                    │  8.更新子任务状态      │                     │
 │                    │─────────────────────→│                     │
 │                    │  POST /sub-tasks/     │                     │
 │                    │  {id}/submit          │                     │
 │                    │                      │                     │
 │                    │  9.触发评审流程        │                     │
 │                    │  (通知reviewer)        │                     │
 │                    │                      │                     │
 │  10.任务完成        │                      │                     │
 │←───────────────────│                      │                     │
 │  {task_id, status, │                      │                     │
 │   output, review}  │                      │                     │
```

#### 2.1.2 详细调用链

**步骤1：用户创建任务**
```http
POST /api/tasks/instantiate
Content-Type: application/json
Authorization: Bearer <user_token>

{
    "template_id": "project-dev-workflow-v1",
    "parameters": {
        "project_name": "AI教育平台",
        "team_size": 5
    }
}
```

**步骤2：Backend加载模板**
```python
# Backend内部处理
template = TemplateEngine.load("project-dev-workflow-v1")
task = template.instantiate({
    "project_name": "AI教育平台",
    "team_size": 5
})
trace_id = generate_trace_id()
task.trace_id = trace_id
```

**步骤3：Backend任务分解**
```python
# Backend内部处理
decomposition_strategy = ProjectDecomposition()
sub_tasks = decomposition_strategy.decompose(task, context={
    "template": template,
    "parameters": task.parameters
})

for sub_task in sub_tasks:
    sub_task.trace_id = trace_id
    sub_task.decomposition_basis = f"基于模板{template.id}分解"
```

**步骤4：Backend创建子任务（OpenMOSS）**
```http
POST http://openmoss:6565/sub-tasks
Content-Type: application/json
X-Agent-Key: <planner_token>

{
    "task_id": "task_001",
    "name": "需求收集",
    "description": "收集AI教育平台的用户需求",
    "deliverable": "需求文档",
    "acceptance": "输出至少10个用户需求点",
    "priority": "high",
    "assigned_agent": "executor_001",
    "type": "once"
}

Response:
{
    "id": "sub_task_001",
    "task_id": "task_001",
    "name": "需求收集",
    "status": "pending",
    "assigned_agent": "executor_001",
    "created_at": "2026-04-21T23:30:00"
}
```

**步骤5：Backend主动派发任务（OpenClaw）**
```http
POST http://openclaw:18789/api/v1/message
Content-Type: application/json
Authorization: Bearer <gateway_token>

{
    "channel": "api",
    "message": "请执行任务：需求收集。\n\n任务描述：收集AI教育平台的用户需求\n交付物：需求文档\n验收标准：输出至少10个用户需求点\n\n请开始执行并输出结果。",
    "conversation_id": "conv_executor_001_sub_task_001",
    "wait_for_response": true,
    "timeout_ms": 300000
}

Response:
{
    "id": "msg_resp_001",
    "conversation_id": "conv_executor_001_sub_task_001",
    "role": "assistant",
    "content": "已完成需求收集，以下是10个用户需求点：\n1. ...\n2. ...\n...",
    "tokens": {"input": 150, "output": 500, "total": 650},
    "latency_ms": 15000,
    "model": "claude-opus-4-6"
}
```

**步骤6：OpenClaw执行任务**
```
OpenClaw内部处理：
1. 接收消息，创建会话（conversation_id）
2. 加载Agent配置（模型、技能、工具）
3. LLM处理消息，生成执行计划
4. 调用工具（web_search、file_write等）
5. 汇总结果，返回响应
```

**步骤7：Backend更新子任务状态（OpenMOSS）**
```http
# 7.1 开始执行
POST http://openmoss:6565/sub-tasks/sub_task_001/start
X-Agent-Key: <executor_token>

{
    "session_id": "conv_executor_001_sub_task_001"
}

# 7.2 提交成果
POST http://openmoss:6565/sub-tasks/sub_task_001/submit
X-Agent-Key: <executor_token>

Response:
{
    "id": "sub_task_001",
    "status": "review",
    "updated_at": "2026-04-21T23:35:00"
}
```

**步骤8：Backend触发评审流程**
```python
# Backend内部处理
review_engine.trigger_review(
    sub_task_id="sub_task_001",
    output=result["content"],
    acceptance_criteria=["输出至少10个用户需求点"]
)

# 通知reviewer Agent（通过OpenMOSS）
notify_reviewer(
    reviewer_id="reviewer_001",
    sub_task_id="sub_task_001",
    output=result["content"]
)
```

**步骤9：Reviewer审查（OpenMOSS）**
```http
# Reviewer Agent被cron唤醒（每20分钟）
GET http://openmoss:6565/sub-tasks?status=review
X-Agent-Key: <reviewer_token>

# 审查通过后
POST http://openmoss:6565/sub-tasks/sub_task_001/complete
X-Agent-Key: <reviewer_token>

Response:
{
    "id": "sub_task_001",
    "status": "done",
    "completed_at": "2026-04-21T23:40:00"
}
```

**步骤10：Backend同步状态并返回结果**
```python
# Backend轮询OpenMOSS状态
sub_task = openmoss_client.get_sub_task("sub_task_001")

if sub_task.status == "done":
    # 更新Backend数据库
    backend_db.update_task(
        task_id="task_001",
        status="completed",
        output=sub_task.output,
        review_result="approved",
        completed_at=datetime.now()
    )
    
    # 返回结果给用户
    return {
        "task_id": "task_001",
        "status": "completed",
        "output": sub_task.output,
        "review": "approved"
    }
```

---

### 场景2：动态任务分解与派发

#### 2.2.1 流程图

```
用户                Backend                OpenMOSS              OpenClaw
 │                    │                      │                     │
 │  1.提交动态任务     │                      │                     │
 │───────────────────→│                      │                     │
 │  {name, type,      │                      │                     │
 │   input_data}      │                      │                     │
 │                    │                      │                     │
 │                    │  2.选择分解策略        │                     │
 │                    │  BugFixDecomposition  │                     │
 │                    │                      │                     │
 │                    │  3.分析Bug报告        │                     │
 │                    │  提取根因             │                     │
 │                    │                      │                     │
 │                    │  4.创建子任务          │                     │
 │                    │  (记录分解依据)        │                     │
 │                    │                      │                     │
 │                    │  5.创建OpenMOSS子任务  │                     │
 │                    │─────────────────────→│                     │
 │                    │  POST /sub-tasks      │                     │
 │                    │  {task_id, name,      │                     │
 │                    │   decomposition_basis}│                     │
 │                    │                      │                     │
 │                    │  6.并行派发子任务      │                     │
 │                    │────────────────────────────────────────────→│
 │                    │  POST /api/v1/message │                     │
 │                    │  (多个子任务并行)      │                     │
 │                    │                      │                     │
 │                    │  7.等待所有结果        │                     │
 │                    │←────────────────────────────────────────────│
 │                    │                      │                     │
 │                    │  8.汇总结果           │                     │
 │                    │  更新OpenMOSS状态      │                     │
 │                    │─────────────────────→│                     │
 │                    │                      │                     │
 │  9.任务完成         │                      │                     │
 │←───────────────────│                      │                     │
```

#### 2.2.2 详细调用链

**步骤1：用户提交动态任务**
```http
POST /api/tasks
Content-Type: application/json
Authorization: Bearer <user_token>

{
    "name": "修复登录Bug",
    "type": "dynamic",
    "input_data": {
        "bug_report": "用户反馈登录时偶尔出现500错误",
        "error_logs": "...",
        "affected_users": 15
    }
}
```

**步骤2：Backend选择分解策略**
```python
# Backend内部处理
if task.type == "dynamic" and "bug_report" in task.input_data:
    decomposition_strategy = BugFixDecomposition()
elif task.type == "dynamic" and "prd_document" in task.input_data:
    decomposition_strategy = RequirementDecomposition()
else:
    decomposition_strategy = DefaultDecomposition()
```

**步骤3：Backend分析Bug报告**
```python
# Backend内部处理
root_causes = decomposition_strategy.analyze(task.input_data)

# 示例输出：
root_causes = [
    {
        "id": "root_cause_1",
        "description": "数据库连接池耗尽",
        "severity": "high",
        "fix_approach": "增加连接池大小"
    },
    {
        "id": "root_cause_2",
        "description": "认证服务超时",
        "severity": "medium",
        "fix_approach": "增加超时时间"
    }
]
```

**步骤4：Backend创建子任务**
```python
sub_tasks = []
for cause in root_causes:
    sub_task = Task(
        name=f"修复{cause.description}",
        parent_task_id=task.id,
        decomposition_basis=f"基于Bug根因分析{cause.id}分解",
        input_data={"bug_details": cause},
        acceptance_criteria=[f"Bug {cause.id}不再复现"],
        parallel_group="bug_fix",  # 并行组标识
        dependencies=[]
    )
    sub_tasks.append(sub_task)
```

**步骤5：Backend创建OpenMOSS子任务**
```http
# 子任务1
POST http://openmoss:6565/sub-tasks
X-Agent-Key: <planner_token>

{
    "task_id": "task_002",
    "name": "修复数据库连接池耗尽",
    "description": "增加连接池大小，优化连接管理",
    "deliverable": "修复代码+测试报告",
    "acceptance": "Bug root_cause_1不再复现",
    "priority": "high",
    "assigned_agent": "executor_002",
    "type": "once"
}

# 子任务2
POST http://openmoss:6565/sub-tasks
X-Agent-Key: <planner_token>

{
    "task_id": "task_002",
    "name": "修复认证服务超时",
    "description": "增加超时时间，优化重试逻辑",
    "deliverable": "修复代码+测试报告",
    "acceptance": "Bug root_cause_2不再复现",
    "priority": "medium",
    "assigned_agent": "executor_003",
    "type": "once"
}
```

**步骤6：Backend并行派发子任务**
```python
# Backend内部处理
import asyncio

async def dispatch_sub_task(sub_task):
    result = await openclaw_client.send_message(
        conversation_id=f"conv_{sub_task.assigned_agent}_{sub_task.id}",
        message=f"请执行任务：{sub_task.name}\n\n描述：{sub_task.description}\n验收标准：{sub_task.acceptance_criteria[0]}",
        wait_for_response=True,
        timeout_ms=300000
    )
    return result

# 并行派发
results = await asyncio.gather(
    *[dispatch_sub_task(st) for st in sub_tasks],
    return_exceptions=True
)
```

**步骤7：Backend等待所有结果**
```python
# Backend内部处理
all_results = []
for sub_task, result in zip(sub_tasks, results):
    if isinstance(result, Exception):
        all_results.append({
            "sub_task_id": sub_task.id,
            "status": "failed",
            "error": str(result)
        })
    else:
        all_results.append({
            "sub_task_id": sub_task.id,
            "status": "completed",
            "output": result["content"]
        })
```

**步骤8：Backend汇总结果并更新OpenMOSS状态**
```http
# 更新子任务1状态
POST http://openmoss:6565/sub-tasks/sub_task_002/start
X-Agent-Key: <executor_token>

{"session_id": "conv_executor_002_sub_task_002"}

POST http://openmoss:6565/sub-tasks/sub_task_002/submit
X-Agent-Key: <executor_token>

# 更新子任务2状态
POST http://openmoss:6565/sub-tasks/sub_task_003/start
X-Agent-Key: <executor_token>

{"session_id": "conv_executor_003_sub_task_003"}

POST http://openmoss:6565/sub-tasks/sub_task_003/submit
X-Agent-Key: <executor_token>
```

---

### 场景3：定时补偿流程

#### 2.3.1 流程图

```
定时任务(每5分钟)     Backend                OpenMOSS              OpenClaw
 │                    │                      │                     │
 │  1.触发定时任务     │                      │                     │
 │───────────────────→│                      │                     │
 │                    │                      │                     │
 │                    │  2.查询超时子任务      │                     │
 │                    │─────────────────────→│                     │
 │                    │  GET /sub-tasks       │                     │
 │                    │  ?status=in_progress  │                     │
 │                    │  &timeout=600         │                     │
 │                    │                      │                     │
 │                    │  3.返回超时列表        │                     │
 │                    │←─────────────────────│                     │
 │                    │                      │                     │
 │                    │  4.检查OpenClaw会话    │                     │
 │                    │────────────────────────────────────────────→│
 │                    │  GET /conversations/  │                     │
 │                    │  {id}                 │                     │
 │                    │                      │                     │
 │                    │  5.返回会话状态        │                     │
 │                    │←────────────────────────────────────────────│
 │                    │                      │                     │
 │                    │  6.判断处理方式        │                     │
 │                    │  - 完成：提交成果      │                     │
 │                    │  - 失败：重新派发      │                     │
 │                    │  - 超时：标记阻塞      │                     │
 │                    │                      │                     │
 │                    │  7.执行处理           │                     │
 │                    │─────────────────────→│                     │
 │                    │  更新子任务状态        │                     │
 │                    │                      │                     │
 │                    │  8.同步Backend状态    │                     │
 │                    │  (更新数据库)          │                     │
```

#### 2.3.2 详细调用链

**步骤1：定时任务触发**
```python
# Backend内部处理（每5分钟执行）
@celery.task(bind=True, max_retries=3)
def compensation_check(self):
    """定时补偿检查"""
    logger.info("开始定时补偿检查")
    
    # 执行补偿逻辑
    result = await compensation_engine.check()
    
    logger.info(f"补偿检查完成，处理{result['processed']}个任务")
```

**步骤2：Backend查询超时子任务**
```http
GET http://openmoss:6565/sub-tasks?status=in_progress&page_size=0
X-Agent-Key: <admin_token>

Response:
{
    "items": [
        {
            "id": "sub_task_004",
            "task_id": "task_003",
            "name": "架构设计",
            "status": "in_progress",
            "assigned_agent": "executor_004",
            "current_session_id": "conv_executor_004_sub_task_004",
            "updated_at": "2026-04-21T23:20:00",  # 10分钟前
            "acceptance": "输出架构设计文档"
        }
    ],
    "total": 1
}
```

**步骤3：Backend检查OpenClaw会话状态**
```http
GET http://openclaw:18789/api/v1/conversations/conv_executor_004_sub_task_004
Authorization: Bearer <gateway_token>

Response:
{
    "id": "conv_executor_004_sub_task_004",
    "status": "completed",  # 或 "in_progress", "failed"
    "last_message_at": "2026-04-21T23:25:00",
    "message_count": 15
}
```

**步骤4：Backend判断处理方式**
```python
# Backend内部处理
for sub_task in timeout_tasks:
    conversation_status = openclaw_client.get_conversation_status(
        sub_task["current_session_id"]
    )
    
    if conversation_status == "completed":
        # 情况1：会话已完成，但OpenMOSS状态未更新
        # → 获取执行结果，提交成果
        history = openclaw_client.get_conversation_history(
            sub_task["current_session_id"]
        )
        output = extract_final_output(history)
        
        openmoss_client.submit_sub_task(
            sub_task_id=sub_task["id"],
            executor_token=get_agent_token(sub_task["assigned_agent"], "executor")
        )
        
    elif conversation_status == "failed":
        # 情况2：会话失败，重新派发任务
        openclaw_client.send_message(
            conversation_id=sub_task["current_session_id"],
            message=f"任务执行失败，请重新执行：{sub_task['name']}",
            wait_for_response=True,
            timeout_ms=300000
        )
        
    elif conversation_status == "in_progress":
        # 情况3：会话仍在执行，但超时
        # → 标记为阻塞，通知管理员
        openmoss_client.block_sub_task(
            sub_task_id=sub_task["id"],
            patrol_token=get_agent_token("patrol_001", "patrol")
        )
        
        notify_admin(
            f"子任务{sub_task['id']}超时阻塞，请处理"
        )
```

**步骤5：Backend同步状态**
```python
# Backend内部处理
async def sync_backend_openmoss_status():
    """同步Backend和OpenMOSS的状态"""
    
    # 获取Backend中所有in_progress的任务
    backend_tasks = await backend_db.list_tasks(status="in_progress")
    
    # 获取OpenMOSS中所有子任务状态
    openmoss_tasks = await openmoss_client.list_all_sub_tasks()
    
    # 对比状态，找出差异
    for backend_task in backend_tasks:
        openmoss_task = find_matching_openmoss_task(backend_task, openmoss_tasks)
        
        if openmoss_task:
            if backend_task["status"] != openmoss_task["status"]:
                # 状态不一致，以OpenMOSS为准
                await backend_db.update_task(
                    task_id=backend_task["id"],
                    status=openmoss_task["status"],
                    updated_at=datetime.now()
                )
                
                logger.info(
                    f"同步任务状态：{backend_task['id']} "
                    f"{backend_task['status']} → {openmoss_task['status']}"
                )
```

---

### 场景4：评审流程

#### 2.4.1 流程图

```
Backend             OpenMOSS              OpenClaw            评审组
 │                    │                     │                   │
 │  1.提交评审请求     │                     │                   │
 │───────────────────→│                     │                   │
 │  POST /review/     │                     │                   │
 │  {sub_task_id,     │                     │                   │
 │   output,          │                     │                   │
 │   criteria}        │                     │                   │
 │                    │                     │                   │
 │                    │  2.创建评审记录      │                   │
 │                    │  加入评审队列         │                   │
 │                    │                     │                   │
 │                    │  3.通知reviewer      │                   │
 │                    │  (cron唤醒)          │                   │
 │                    │─────────────────────────────────────────→│
 │                    │                     │                   │
 │                    │                     │                   │  4.执行评审
 │                    │                     │                   │  (检查验收标准)
 │                    │                     │                   │
 │                    │                     │                   │  5.提交评审结果
 │                    │←─────────────────────────────────────────│
 │                    │  POST /review/      │                   │
 │                    │  {id}/complete      │                   │
 │                    │  {status: "approved"│                   │
 │                    │   comments:"..."}   │                   │
 │                    │                     │                   │
 │  6.评审结果通知     │                     │                   │
 │←───────────────────│                     │                   │
 │  {sub_task_id,     │                     │                   │
 │   status:"approved"│                     │                   │
 │   comments:"..."}  │                     │                   │
 │                    │                     │                   │
 │  7.触发后续任务     │                     │                   │
 │  (如有依赖任务)      │                     │                   │
```

#### 2.4.2 详细调用链

**步骤1：Backend提交评审请求**
```http
POST /api/reviews
Content-Type: application/json
Authorization: Bearer <user_token>

{
    "sub_task_id": "sub_task_001",
    "output": "已完成需求收集，以下是10个用户需求点：...",
    "acceptance_criteria": [
        "输出至少10个用户需求点",
        "需求点需包含优先级评估"
    ],
    "reviewer_ids": ["reviewer_001", "reviewer_002"]
}
```

**步骤2：OpenMOSS创建评审记录**
```python
# OpenMOSS内部处理
review_record = ReviewRecord(
    sub_task_id="sub_task_001",
    output="已完成需求收集...",
    acceptance_criteria=[...],
    reviewer_ids=["reviewer_001", "reviewer_002"],
    status="pending",
    created_at=datetime.now()
)
db.add(review_record)
db.commit()
```

**步骤3：OpenMOSS通知reviewer**
```
# Reviewer Agent被cron唤醒（每20分钟）
GET http://openmoss:6565/reviews?status=pending
X-Agent-Key: <reviewer_token>

Response:
{
    "items": [
        {
            "id": "review_001",
            "sub_task_id": "sub_task_001",
            "output": "已完成需求收集...",
            "acceptance_criteria": [...]
        }
    ]
}
```

**步骤4：Reviewer执行评审**
```python
# Reviewer Agent内部处理（通过OpenClaw执行）
def execute_review(review_record):
    """执行评审"""
    
    # 1. 检查每个验收标准
    results = []
    for criterion in review_record.acceptance_criteria:
        result = check_criterion(criterion, review_record.output)
        results.append({
            "criterion": criterion,
            "passed": result["passed"],
            "evidence": result["evidence"]
        })
    
    # 2. 汇总评审结果
    all_passed = all(r["passed"] for r in results)
    
    if all_passed:
        return {
            "status": "approved",
            "comments": "所有验收标准均满足",
            "details": results
        }
    else:
        failed_criteria = [r["criterion"] for r in results if not r["passed"]]
        return {
            "status": "rejected",
            "comments": f"以下验收标准未满足：{', '.join(failed_criteria)}",
            "details": results
        }
```

**步骤5：Reviewer提交评审结果**
```http
POST http://openmoss:6565/reviews/review_001/complete
X-Agent-Key: <reviewer_token>

{
    "status": "approved",
    "comments": "所有验收标准均满足",
    "details": [
        {
            "criterion": "输出至少10个用户需求点",
            "passed": true,
            "evidence": "实际输出12个需求点"
        },
        {
            "criterion": "需求点需包含优先级评估",
            "passed": true,
            "evidence": "每个需求点均标注了优先级"
        }
    ]
}
```

**步骤6：Backend接收评审结果**
```python
# Backend轮询OpenMOSS获取评审结果
review_result = openmoss_client.get_review_result("review_001")

if review_result["status"] == "approved":
    # 评审通过，更新任务状态
    backend_db.update_task(
        task_id="task_001",
        review_status="approved",
        review_comments=review_result["comments"],
        updated_at=datetime.now()
    )
    
    # 触发后续任务
    trigger_next_tasks("task_001")
    
else:
    # 评审驳回，任务回退
    backend_db.update_task(
        task_id="task_001",
        status="rework",
        review_status="rejected",
        review_comments=review_result["comments"],
        updated_at=datetime.now()
    )
    
    # 通知开发者修改
    notify_developer(
        f"任务{task_001}评审驳回，请根据意见修改：{review_result['comments']}"
    )
```

---

### 场景5：异常处理和回滚

#### 2.5.1 流程图

```
Backend             OpenMOSS              OpenClaw
 │                    │                     │
 │  1.任务执行失败     │                     │
 │←─────────────────────────────────────────│
 │  (超时/异常/LLM错误) │                     │
 │                    │                     │
 │  2.标记任务失败     │                     │
 │───────────────────→│                     │
 │  POST /sub-tasks/  │                     │
 │  {id}/block        │                     │
 │                    │                     │
 │  3.记录错误日志     │                     │
 │  (Trace ID关联)    │                     │
 │                    │                     │
 │  4.判断重试策略     │                     │
 │  - 可重试：重新派发  │                     │
 │  - 不可重试：通知用户│                     │
 │                    │                     │
 │  5.重新派发任务     │                     │
 │─────────────────────────────────────────→│
 │  POST /api/v1/     │                     │
 │  message           │                     │
 │  (重试指令)         │                     │
 │                    │                     │
 │  6.返回重试结果     │                     │
 │←─────────────────────────────────────────│
 │                    │                     │
 │  7.更新任务状态     │                     │
 │───────────────────→│                     │
```

#### 2.5.2 详细调用链

**步骤1：任务执行失败**
```python
# Backend内部处理
try:
    result = await openclaw_client.send_message(
        conversation_id=conversation_id,
        message=task_instruction,
        wait_for_response=True,
        timeout_ms=300000
    )
except requests.exceptions.Timeout:
    # 超时错误
    error_info = {
        "type": "timeout",
        "message": f"任务执行超时（{300000}ms）",
        "trace_id": trace_id,
        "timestamp": datetime.now()
    }
    
    # 记录错误日志
    logger.error(f"任务执行失败：{error_info}")
    
    # 触发异常处理流程
    await handle_task_failure(sub_task_id, error_info)
    
except Exception as e:
    # 其他异常
    error_info = {
        "type": "exception",
        "message": str(e),
        "trace_id": trace_id,
        "timestamp": datetime.now()
    }
    
    await handle_task_failure(sub_task_id, error_info)
```

**步骤2：Backend标记任务失败**
```http
POST http://openmoss:6565/sub-tasks/sub_task_001/block
X-Agent-Key: <patrol_token>

Response:
{
    "id": "sub_task_001",
    "status": "blocked",
    "blocked_at": "2026-04-21T23:45:00"
}
```

**步骤3：Backend记录错误日志**
```python
# Backend内部处理
error_log = ErrorLog(
    trace_id=trace_id,
    task_id="task_001",
    sub_task_id="sub_task_001",
    error_type=error_info["type"],
    error_message=error_info["message"],
    timestamp=error_info["timestamp"],
    retry_count=0,
    max_retries=3
)
backend_db.add(error_log)
```

**步骤4：Backend判断重试策略**
```python
# Backend内部处理
def should_retry(error_log):
    """判断是否应该重试"""
    
    # 1. 检查重试次数
    if error_log.retry_count >= error_log.max_retries:
        return False, "达到最大重试次数"
    
    # 2. 检查错误类型
    if error_log.error_type in ["timeout", "rate_limit"]:
        return True, "可重试错误"
    elif error_log.error_type in ["auth_error", "invalid_config"]:
        return False, "不可重试错误（配置问题）"
    else:
        return True, "默认可重试"

should_retry, reason = should_retry(error_log)

if should_retry:
    # 重新派发任务
    await retry_task(sub_task_id, error_log)
else:
    # 通知用户
    notify_user(
        f"任务{sub_task_id}执行失败，原因：{reason}",
        level="error"
    )
```

**步骤5：Backend重新派发任务**
```http
# 重新派发任务
POST http://openclaw:18789/api/v1/message
Authorization: Bearer <gateway_token>

{
    "channel": "api",
    "message": "任务执行失败，请重新执行：需求收集\n\n失败原因：超时\n\n请重新开始执行并输出结果。",
    "conversation_id": "conv_executor_001_sub_task_001",
    "wait_for_response": true,
    "timeout_ms": 300000
}
```

**步骤6：Backend更新重试次数**
```python
# Backend内部处理
error_log.retry_count += 1
error_log.last_retry_at = datetime.now()
backend_db.commit()
```

---

## 三、数据流和状态同步

### 3.1 数据流图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流向                                        │
└─────────────────────────────────────────────────────────────────────────────┘

用户请求
  │
  ▼
Backend API
  │
  ├──→ Backend数据库（任务模板、任务实例、评审记录、Trace日志）
  │
  ├──→ OpenMOSS API（任务队列、Agent注册、审查流程）
  │       │
  │       └──→ OpenMOSS数据库（子任务状态、Agent身份、审查记录）
  │
  └──→ OpenClaw API（消息发送、工具调用、会话管理）
          │
          └──→ OpenClaw文件系统（会话上下文、记忆、技能）
```

### 3.2 状态同步机制

```python
class StateSyncEngine:
    """状态同步引擎"""
    
    async def sync(self):
        """定期同步Backend和OpenMOSS的状态"""
        
        # 1. 获取Backend中所有活跃任务
        backend_tasks = await backend_db.list_tasks(
            status__in=["pending", "in_progress", "reviewing"]
        )
        
        # 2. 获取OpenMOSS中所有子任务状态
        openmoss_tasks = await openmoss_client.list_all_sub_tasks()
        
        # 3. 对比状态，找出差异
        differences = self.find_differences(backend_tasks, openmoss_tasks)
        
        # 4. 同步状态（以OpenMOSS为准）
        for diff in differences:
            await backend_db.update_task(
                task_id=diff["task_id"],
                status=diff["openmoss_status"],
                updated_at=datetime.now()
            )
            
            logger.info(
                f"同步任务状态：{diff['task_id']} "
                f"{diff['backend_status']} → {diff['openmoss_status']}"
            )
        
        # 5. 记录同步日志
        await sync_log.create(
            synced_count=len(differences),
            timestamp=datetime.now()
        )
    
    def find_differences(self, backend_tasks, openmoss_tasks):
        """找出状态差异"""
        differences = []
        
        for backend_task in backend_tasks:
            openmoss_task = self.find_matching_task(backend_task, openmoss_tasks)
            
            if openmoss_task:
                if backend_task["status"] != openmoss_task["status"]:
                    differences.append({
                        "task_id": backend_task["id"],
                        "backend_status": backend_task["status"],
                        "openmoss_status": openmoss_task["status"]
                    })
        
        return differences
```

---

## 四、异常场景处理

### 4.1 异常场景列表

| 场景 | 处理方式 | 负责组件 |
|------|---------|---------|
| OpenClaw执行超时 | 标记为blocked，定时补偿重新派发 | Backend |
| OpenMOSS状态不一致 | 定时同步，以OpenMOSS为准 | Backend |
| Agent不可用 | 重新分配Agent，通知管理员 | Backend + OpenMOSS |
| 评审驳回 | 任务回退到in_progress，通知开发者 | Backend |
| 网络异常 | 重试机制，最多3次 | Backend |
| LLM返回错误 | 记录错误，重新派发 | Backend + OpenClaw |
| 任务依赖未满足 | 等待依赖完成，定时检查 | Backend |

### 4.2 重试策略

```python
class RetryStrategy:
    """重试策略"""
    
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2  # 指数退避
    
    @classmethod
    def should_retry(cls, error_type: str, retry_count: int) -> bool:
        """判断是否应该重试"""
        
        if retry_count >= cls.MAX_RETRIES:
            return False
        
        # 可重试的错误类型
        retryable_errors = [
            "timeout",
            "rate_limit",
            "network_error",
            "llm_temporary_error"
        ]
        
        return error_type in retryable_errors
    
    @classmethod
    def get_wait_time(cls, retry_count: int) -> int:
        """获取等待时间（指数退避）"""
        return cls.BACKOFF_FACTOR ** retry_count  # 2, 4, 8秒
```

---

## 五、总结

### 5.1 核心设计原则

| 原则 | 说明 |
|------|------|
| **Backend为主** | Backend负责任务模板、分解、派发、评审，是核心大脑 |
| **OpenMOSS为辅** | OpenMOSS负责任务队列持久化、Agent注册、审查流程 |
| **OpenClaw执行** | OpenClaw负责Agent运行时、工具执行、会话管理 |
| **主动派发** | Backend直接调用OpenClaw API派发任务，实时响应 |
| **定时补偿** | 每5分钟检查OpenMOSS状态，发现超时重新派发 |
| **状态同步** | 定期同步Backend和OpenMOSS状态，以OpenMOSS为准 |
| **Trace追踪** | 全链路Trace ID，便于问题排查 |

### 5.2 关键API调用总结

| 调用方向 | API | 用途 | 频率 |
|---------|-----|------|------|
| Backend → OpenMOSS | `POST /sub-tasks` | 创建子任务 | 按需 |
| Backend → OpenMOSS | `POST /sub-tasks/{id}/submit` | 提交成果 | 按需 |
| Backend → OpenMOSS | `GET /sub-tasks` | 查询子任务 | 每5分钟 |
| Backend → OpenClaw | `POST /api/v1/message` | 派发任务 | 按需 |
| Backend → OpenClaw | `GET /conversations/{id}` | 查询会话状态 | 每5分钟 |
| OpenMOSS → OpenClaw | (通过Agent cron) | Agent执行任务 | 每15-30分钟 |

### 5.3 下一步行动

1. **部署实际环境**：Docker Compose部署OpenMOSS + OpenClaw
2. **运行验证脚本**：执行`code/scripts/verify_api.py`
3. **编写适配层代码**：OpenMOSSClient和OpenClawClient封装
4. **端到端测试**：验证5个核心场景的完整流程
5. **性能优化**：优化状态同步频率、重试策略、超时设置

---

*推演完成时间：2026-04-21 23:30*
*下次更新：实际环境验证后*
