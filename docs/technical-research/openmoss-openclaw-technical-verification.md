# OpenMOSS & OpenClaw 技术验证报告（详细版）

> 调研日期：2026-04-21 23:14
> 调研目的：详细验证OpenMOSS和OpenClaw的API能力，确认主动派发任务的可行性

---

## 一、OpenMOSS 详细API分析

### 1.1 任务管理API（tasks.py）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/tasks` | 任意Agent | 分页查询任务列表 |
| GET | `/tasks/{task_id}` | 任意Agent | 获取任务详情 |
| POST | `/tasks` | planner | 创建任务 |
| PUT | `/tasks/{task_id}` | planner | 编辑任务（仅planning/active状态） |
| PUT | `/tasks/{task_id}/status` | planner | 更新任务状态 |
| POST | `/tasks/{task_id}/cancel` | planner | 取消任务 |
| POST | `/tasks/{task_id}/modules` | planner | 创建模块 |
| GET | `/tasks/{task_id}/modules` | 任意Agent | 查看模块列表 |

**关键发现**：
- 任务创建**仅限planner角色**，Backend无法直接使用admin token创建
- 无独立的"派发"API，派发通过状态更新或模块/子任务分配实现
- 任务状态：`planning` → `active` → `in_progress` → `completed` → `archived/cancelled`

### 1.2 子任务管理API（sub_tasks.py）

| 方法 | 路径 | 权限 | 状态流转 | 说明 |
|------|------|------|---------|------|
| POST | `/sub-tasks` | planner | - | 创建子任务 |
| GET | `/sub-tasks` | 任意Agent | - | 查询子任务列表 |
| GET | `/sub-tasks/mine` | 任意Agent | - | 查看我的子任务 |
| GET | `/sub-tasks/available` | 任意Agent | - | 查看待认领子任务 |
| GET | `/sub-tasks/latest` | 任意Agent | - | 获取最新子任务 |
| GET | `/sub-tasks/{id}` | 任意Agent | - | 获取子任务详情 |
| POST | `/sub-tasks/{id}/claim` | executor | pending→assigned | 认领子任务 |
| POST | `/sub-tasks/{id}/start` | executor | assigned/rework→in_progress | 开始执行 |
| POST | `/sub-tasks/{id}/submit` | executor | in_progress→review | 提交成果 |
| POST | `/sub-tasks/{id}/complete` | reviewer | review→done | 审查通过 |
| POST | `/sub-tasks/{id}/rework` | reviewer | review→rework | 驳回返工 |
| POST | `/sub-tasks/{id}/block` | patrol | 任意→blocked | 标记异常 |
| POST | `/sub-tasks/{id}/reassign` | planner | blocked→assigned | 重新分配 |
| PUT | `/sub-tasks/{id}` | planner | - | 编辑子任务 |
| POST | `/sub-tasks/{id}/cancel` | planner | - | 取消子任务 |
| POST | `/sub-tasks/{id}/session` | executor | - | 更新会话ID |

**关键发现**：
- 子任务创建**仅限planner角色**
- 子任务认领**仅限executor角色**
- 子任务提交**仅限executor角色**
- 审查通过/驳回**仅限reviewer角色**
- 重新分配**仅限planner角色**
- 每个子任务可绑定`session_id`（OpenClaw会话ID）
- 支持`assigned_agent`字段指定执行Agent

### 1.3 认证机制

| 角色 | Header | 获取方式 |
|------|--------|---------|
| Admin | `X-Admin-Token` | 通过`/login`接口获取 |
| Agent | `X-Agent-Key` | Agent注册后获取（`om_`开头） |
| 注册 | `X-Registration-Token` | config.yaml中配置 |

### 1.4 主动派发可行性分析

**方案A：通过OpenMOSS API派发**

```python
# 1. Backend使用planner token创建子任务
POST /sub-tasks
Headers: {X-Agent-Key: <planner_token>}
Body: {
    "task_id": "task_001",
    "name": "需求收集",
    "assigned_agent": "executor_001",  # 指定执行Agent
    "acceptance": "输出需求文档"
}

# 2. Backend使用executor token认领子任务
POST /sub-tasks/{id}/claim
Headers: {X-Agent-Key: <executor_token>}
Body: {"session_id": "conv_001"}

# 3. Backend使用executor token开始执行
POST /sub-tasks/{id}/start
Headers: {X-Agent-Key: <executor_token>}
Body: {"session_id": "conv_001"}
```

**问题**：
- Backend需要管理多个Agent token（planner、executor、reviewer）
- 需要模拟Agent行为（认领、开始、提交）
- 违背OpenMOSS的设计初衷（Agent自主认领）

**方案B：Backend直接调用OpenClaw API（推荐）**

```python
# 1. Backend创建子任务（使用planner token）
POST /sub-tasks
Body: {
    "task_id": "task_001",
    "name": "需求收集",
    "assigned_agent": "executor_001",
    "status": "assigned"  # 直接设置为assigned
}

# 2. Backend直接调用OpenClaw发送任务指令
POST http://openclaw:18789/api/v1/message
Headers: {Authorization: Bearer <gateway_token>}
Body: {
    "channel": "api",
    "message": "请执行任务：需求收集。验收标准：输出需求文档",
    "conversation_id": "conv_executor_001",
    "wait_for_response": true,
    "timeout_ms": 300000
}

# 3. OpenClaw执行完成后，Backend更新子任务状态
POST /sub-tasks/{id}/submit
Headers: {X-Agent-Key: <executor_token>}
```

**优势**：
- Backend直接控制任务派发，无需等待cron唤醒
- 实时响应，延迟取决于OpenClaw执行时间
- 简化流程，无需模拟Agent行为

---

## 二、OpenClaw 详细API分析

### 2.1 Gateway REST API

**Base URL**: `http://127.0.0.1:18789/api/v1`

| 方法 | 路径 | 说明 | 关键参数 |
|------|------|------|---------|
| GET | `/health` | 健康检查 | 无 |
| GET | `/status` | 系统状态 | 无 |
| POST | `/message` | 发送消息 | channel, message, conversation_id, wait_for_response, timeout_ms |
| GET | `/conversations` | 列出对话 | limit, offset, channel, since, until |
| GET | `/conversations/:id` | 获取对话历史 | 无 |
| DELETE | `/conversations/:id` | 删除对话 | 无 |
| GET | `/memory/stats` | 记忆统计 | 无 |
| POST | `/memory/search` | 搜索记忆 | query, limit, type, since, until |
| DELETE | `/memory/prune` | 清理记忆 | 条件参数 |
| GET | `/skills` | 列出技能 | 无 |
| POST | `/skills/install` | 安装技能 | 技能信息 |
| DELETE | `/skills/:name` | 删除技能 | 无 |
| GET | `/channels` | 列出渠道 | 无 |
| GET | `/channels/:type/status` | 渠道状态 | 无 |
| GET | `/config` | 获取配置 | 无 |
| PUT | `/config` | 更新配置 | 配置参数 |
| GET | `/logs` | 获取日志 | lines, level, component |

### 2.2 工具调用API

**端点**: `POST /tools/invoke`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tool` | string | ✅ | 工具名称 |
| `action` | string | ❌ | 工具动作 |
| `args` | object | ❌ | 工具参数 |
| `sessionKey` | string | ❌ | 会话键（默认"main"） |

**默认禁止的工具**：exec, shell, fs_write, fs_delete, gateway, cron, sessions_spawn

### 2.3 消息发送API详解

**端点**: `POST /api/v1/message`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `channel` | string | ✅ | - | 消息渠道（如"api"） |
| `message` | string | ✅ | - | 消息内容 |
| `conversation_id` | string | ❌ | - | 对话ID（省略则新建） |
| `metadata` | object | ❌ | - | 附加上下文 |
| `wait_for_response` | boolean | ❌ | true | 是否等待响应 |
| `timeout_ms` | integer | ❌ | 30000 | 超时时间（毫秒） |

**三种调用模式**：

1. **同步模式**（默认）
   - `wait_for_response: true`
   - 阻塞等待Agent回复
   - 适用于短耗时任务

2. **异步模式**
   - `wait_for_response: false`
   - 立即返回`poll_url`
   - 适用于长耗时任务

3. **流式模式**（SSE）
   - `Accept: text/event-stream`
   - 逐块推送响应
   - 适用于实时展示

### 2.4 主动派发可行性分析

**✅ 完全可行**

```python
# Backend直接调用OpenClaw派发任务
import requests

def dispatch_task_to_agent(agent_conversation_id: str, task_instruction: str, 
                          wait_for_result: bool = True, timeout_ms: int = 300000):
    """
    主动派发任务到Agent
    
    Args:
        agent_conversation_id: Agent的对话ID（用于保持上下文）
        task_instruction: 任务指令
        wait_for_result: 是否等待结果
        timeout_ms: 超时时间
    """
    url = "http://127.0.0.1:18789/api/v1/message"
    headers = {
        "Authorization": "Bearer <gateway_token>",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": "api",
        "message": task_instruction,
        "conversation_id": agent_conversation_id,
        "wait_for_response": wait_for_result,
        "timeout_ms": timeout_ms
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=timeout_ms/1000 + 10)
    return response.json()

# 使用示例
result = dispatch_task_to_agent(
    agent_conversation_id="conv_executor_001",
    task_instruction="请执行任务：需求收集。验收标准：输出需求文档",
    wait_for_result=True,
    timeout_ms=300000  # 5分钟超时
)
```

---

## 三、主动派发 + 定时补偿方案

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Backend（自研）                         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               任务派发引擎                             │   │
│  │                                                      │   │
│  │  1. 创建任务 → 分解子任务 → 设置验收标准              │   │
│  │  2. 主动派发：调用OpenClaw API发送任务指令            │   │
│  │  3. 同步结果：更新OpenMOSS子任务状态                  │   │
│  │  4. 触发评审：调用OpenMOSS审查接口                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               定时补偿引擎                             │   │
│  │                                                      │   │
│  │  1. 定期检查OpenMOSS子任务状态（每5分钟）             │   │
│  │  2. 发现超时/阻塞任务，重新派发                       │   │
│  │  3. 同步OpenMOSS和Backend的状态                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                                      │
         │ 主动派发（实时）                      │ 定时补偿（每5分钟）
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│      OpenClaw       │              │      OpenMOSS       │
│  - 接收任务指令      │              │  - 任务队列管理      │
│  - 执行任务          │              │  - 状态持久化        │
│  - 返回结果          │              │  - 审查流程          │
└─────────────────────┘              └─────────────────────┘
```

### 3.2 主动派发流程

```python
async def dispatch_task_flow(task_id: str, sub_task_id: str, agent_id: str, 
                            instruction: str, acceptance_criteria: list[str]):
    """
    主动派发任务流程
    """
    # 1. 创建OpenClaw会话（或使用已有会话）
    conversation_id = f"conv_{agent_id}_{sub_task_id}"
    
    # 2. 构建任务指令
    task_instruction = f"""
任务：{instruction}
验收标准：
{chr(10).join(f'- {c}' for c in acceptance_criteria)}
请执行任务并输出结果。
"""
    
    # 3. 主动派发任务到Agent（同步等待结果）
    result = await openclaw_client.send_message(
        conversation_id=conversation_id,
        message=task_instruction,
        wait_for_response=True,
        timeout_ms=300000  # 5分钟超时
    )
    
    # 4. 解析执行结果
    if result and result.get("content"):
        output = result["content"]
        
        # 5. 更新OpenMOSS子任务状态为review
        await openmoss_client.submit_sub_task(
            sub_task_id=sub_task_id,
            executor_token=get_agent_token(agent_id, "executor")
        )
        
        # 6. 记录执行结果
        await save_task_output(sub_task_id, output)
        
        return {"status": "submitted", "output": output}
    else:
        # 7. 执行失败，标记为blocked
        await openmoss_client.block_sub_task(
            sub_task_id=sub_task_id,
            patrol_token=get_agent_token("patrol_001", "patrol")
        )
        
        return {"status": "failed"}
```

### 3.3 定时补偿流程

```python
async def compensation_check():
    """
    定时补偿检查（每5分钟执行）
    """
    # 1. 查询OpenMOSS中超时的子任务
    timeout_sub_tasks = await openmoss_client.list_sub_tasks(
        status="in_progress",
        timeout_threshold=600  # 10分钟超时
    )
    
    for sub_task in timeout_sub_tasks:
        # 2. 检查OpenClaw会话状态
        conversation_id = sub_task.get("current_session_id")
        if conversation_id:
            status = await openclaw_client.get_conversation_status(conversation_id)
            
            if status == "completed":
                # 3. 获取执行结果
                result = await openclaw_client.get_conversation_history(conversation_id)
                
                # 4. 更新OpenMOSS状态
                await openmoss_client.submit_sub_task(
                    sub_task_id=sub_task["id"]
                )
            elif status == "failed":
                # 5. 重新派发任务
                await dispatch_task_flow(
                    task_id=sub_task["task_id"],
                    sub_task_id=sub_task["id"],
                    agent_id=sub_task["assigned_agent"],
                    instruction=sub_task["description"],
                    acceptance_criteria=[sub_task["acceptance"]]
                )
    
    # 6. 同步Backend和OpenMOSS的状态
    await sync_backend_openmoss_status()
```

### 3.4 状态同步机制

```python
async def sync_backend_openmoss_status():
    """
    同步Backend和OpenMOSS的状态
    """
    # 1. 获取Backend中所有in_progress的任务
    backend_tasks = await backend_db.list_tasks(status="in_progress")
    
    # 2. 获取OpenMOSS中所有子任务状态
    openmoss_tasks = await openmoss_client.list_all_sub_tasks()
    
    # 3. 对比状态，找出差异
    for backend_task in backend_tasks:
        openmoss_task = find_matching_openmoss_task(backend_task, openmoss_tasks)
        
        if openmoss_task:
            if backend_task["status"] != openmoss_task["status"]:
                # 4. 状态不一致，以OpenMOSS为准
                await backend_db.update_task(
                    task_id=backend_task["id"],
                    status=openmoss_task["status"],
                    updated_at=datetime.now()
                )
```

---

## 四、技术验证结论

### 4.1 验证结果

| 验证项 | 验证方式 | 结果 | 说明 |
|--------|---------|------|------|
| OpenMOSS健康检查 | 文档调研 | ✅ 可用 | GET /api/health |
| OpenMOSS任务创建 | 源码分析 | ✅ 可用 | 需要planner角色token |
| OpenMOSS子任务管理 | 源码分析 | ✅ 可用 | 完整的CRUD和状态流转 |
| OpenMOSS主动派发 | 源码分析 | ⚠️ 间接支持 | 需通过状态更新模拟派发 |
| OpenClaw健康检查 | 文档调研 | ✅ 可用 | GET /api/v1/health |
| OpenClaw消息发送 | 文档调研 | ✅ 可用 | POST /api/v1/message（同步/异步/SSE） |
| OpenClaw工具调用 | 文档调研 | ✅ 可用 | POST /tools/invoke |
| OpenClaw主动派发 | 文档调研 | ✅ 完全支持 | 直接调用/message即可 |
| 主动派发流程 | 方案设计 | ✅ 可行 | Backend→OpenClaw→OpenMOSS |
| 定时补偿流程 | 方案设计 | ✅ 可行 | 定期检查+重新派发 |

### 4.2 核心结论

**✅ 主动派发完全可行**

- OpenClaw提供完整的HTTP API（POST /api/v1/message）
- 支持同步/异步/SSE三种模式
- Backend可直接调用，无需等待cron唤醒
- 实时响应，延迟取决于LLM执行时间

**✅ 定时补偿可作为兜底**

- Backend定期（每5分钟）检查OpenMOSS状态
- 发现超时/阻塞任务，自动重新派发
- 保持Backend和OpenMOSS状态一致

**⚠️ 需要管理多个Agent token**

- OpenMOSS的API需要不同角色的Agent token
- Backend需要安全存储和管理这些token
- 建议引入token自动刷新机制

### 4.3 下一步行动

1. **部署实际环境**：Docker Compose部署OpenMOSS + OpenClaw
2. **配置Agent**：注册planner、executor、reviewer、patrol角色
3. **运行验证脚本**：执行`code/scripts/verify_api.py`
4. **端到端测试**：验证主动派发+定时补偿完整流程
5. **编写适配层**：封装OpenMOSSClient和OpenClawClient

---

*报告完成时间：2026-04-21 23:30*
*验证脚本路径：`D:\coding\multi-agent-flow\code\scripts\verify_api.py`*
