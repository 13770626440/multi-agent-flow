# 审计日志设计

## 文档信息
- **文档编号**: LOG-001
- **版本**: v1.0
- **创建日期**: 2026 年 4 月 9 日
- **状态**: 已实施
- **作者**: AI Assistant（架构师）

---

## 1. 审计日志架构

### 1.1 日志分类
```
审计日志
├── 认证日志（Authentication Logs）
│   ├── 登录成功/失败
│   ├── 注销
│   └── Token 刷新
├── 授权日志（Authorization Logs）
│   ├── 权限变更
│   ├── 角色分配
│   └── 账户锁定/解锁
├── 数据操作日志（Data Operation Logs）
│   ├── 创建操作
│   ├── 更新操作
│   ├── 删除操作
│   └── 查询操作（敏感数据）
├── 系统日志（System Logs）
│   ├── 配置变更
│   ├── 备份操作
│   └── 异常事件
└── 业务日志（Business Logs）
    ├── 项目创建/删除
    ├── 模板变更
    └── Agent 执行
```

---

## 2. 数据库设计

### 2.1 审计日志表
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 用户信息
    user_id UUID REFERENCES users(id),
    username VARCHAR(50),
    
    -- 操作信息
    action VARCHAR(100) NOT NULL,
    action_category VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    
    -- 时间信息
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    request_body JSONB,
    request_headers JSONB,
    
    -- 响应信息
    response_status INTEGER,
    response_body JSONB,
    response_time_ms INTEGER,
    
    -- 额外信息
    session_id UUID,
    error_message TEXT,
    metadata JSONB,
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_action_category (action_category),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_action_time (action_time),
    INDEX idx_ip_address (ip_address)
);

-- 分区表（按月分区）
CREATE TABLE audit_logs_2026_04 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE audit_logs_2026_05 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
```

### 2.2 日志保留策略
```sql
-- 自动清理 90 天前的日志
CREATE EVENT clean_old_audit_logs
ON SCHEDULE EVERY 1 DAY
DO DELETE FROM audit_logs WHERE action_time < NOW() - INTERVAL '90 days';

-- 归档重要日志（1 年前）
CREATE TABLE audit_logs_archive (
    LIKE audit_logs INCLUDING ALL
);

CREATE EVENT archive_old_logs
ON SCHEDULE EVERY 1 MONTH
DO 
    INSERT INTO audit_logs_archive
    SELECT * FROM audit_logs 
    WHERE action_time < NOW() - INTERVAL '1 year';
```

---

## 3. 审计中间件

### 3.1 审计日志中间件
```python
from fastapi import Request, Response
import time
import json

async def audit_log_middleware(request: Request, call_next):
    """
    审计日志中间件
    记录所有请求的详细信息
    """
    start_time = time.time()
    
    # 1. 记录请求信息
    audit_record = {
        'user_id': getattr(request.state, 'user', {}).get('id'),
        'username': getattr(request.state, 'user', {}).get('username'),
        'action': f"{request.method}:{request.url.path}",
        'action_category': categorize_action(request.url.path),
        'resource_type': extract_resource_type(request.url.path),
        'resource_id': extract_resource_id(request.url.path),
        'action_time': datetime.utcnow(),
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent'),
        'request_method': request.method,
        'request_path': request.url.path,
        'request_headers': dict(request.headers),
    }
    
    # 2. 记录请求体（敏感信息脱敏）
    if request.method in ['POST', 'PUT', 'PATCH']:
        body = await request.body()
        if body:
            try:
                request_data = json.loads(body)
                # 脱敏密码等敏感字段
                request_data = sanitize_request_data(request_data)
                audit_record['request_body'] = request_data
            except:
                pass
    
    # 3. 继续处理请求
    response = await call_next(request)
    
    # 4. 记录响应信息
    duration_ms = int((time.time() - start_time) * 1000)
    audit_record.update({
        'response_status': response.status_code,
        'response_time_ms': duration_ms,
        'session_id': request.cookies.get('session_id'),
    })
    
    # 5. 异步写入数据库（不阻塞请求）
    asyncio.create_task(save_audit_log(audit_record))
    
    return response

def categorize_action(path: str) -> str:
    """
    分类操作类型
    """
    if '/auth/' in path:
        return 'authentication'
    elif '/users/' in path:
        return 'user_management'
    elif '/projects/' in path:
        return 'project_management'
    elif '/templates/' in path:
        return 'template_management'
    elif '/agents/' in path:
        return 'agent_management'
    else:
        return 'general'

def sanitize_request_data(data: dict) -> dict:
    """
    脱敏敏感数据
    """
    sensitive_fields = ['password', 'token', 'secret', 'api_key']
    sanitized = data.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '***REDACTED***'
    
    return sanitized
```

---

## 4. 审计事件

### 4.1 认证事件
```python
# 登录成功
async def log_login_success(user: dict, ip: str):
    await save_audit_log({
        'user_id': user['id'],
        'username': user['username'],
        'action': 'LOGIN_SUCCESS',
        'action_category': 'authentication',
        'ip_address': ip,
        'metadata': {
            'login_method': 'password',
            'user_agent': request.headers.get('user-agent')
        }
    })

# 登录失败
async def log_login_failure(username: str, ip: str, reason: str):
    await save_audit_log({
        'username': username,
        'action': 'LOGIN_FAILURE',
        'action_category': 'authentication',
        'ip_address': ip,
        'error_message': reason
    })

# 注销
async def log_logout(user: dict, ip: str):
    await save_audit_log({
        'user_id': user['id'],
        'username': user['username'],
        'action': 'LOGOUT',
        'action_category': 'authentication',
        'ip_address': ip
    })
```

### 4.2 授权事件
```python
# 分配角色
async def log_role_assignment(operator: dict, user_id: str, role_id: str):
    await save_audit_log({
        'user_id': operator['id'],
        'username': operator['username'],
        'action': 'ROLE_ASSIGNED',
        'action_category': 'authorization',
        'resource_type': 'user',
        'resource_id': user_id,
        'metadata': {
            'role_id': role_id,
            'operator_id': operator['id']
        }
    })

# 账户锁定
async def log_account_lock(user_id: str, reason: str):
    await save_audit_log({
        'user_id': user_id,
        'action': 'ACCOUNT_LOCKED',
        'action_category': 'authorization',
        'metadata': {
            'reason': reason
        }
    })
```

### 4.3 数据操作事件
```python
# 创建资源
async def log_resource_create(user: dict, resource_type: str, resource_id: str, data: dict):
    await save_audit_log({
        'user_id': user['id'],
        'username': user['username'],
        'action': 'RESOURCE_CREATED',
        'action_category': 'data_operation',
        'resource_type': resource_type,
        'resource_id': resource_id,
        'request_body': sanitize_data(data)
    })

# 更新资源
async def log_resource_update(user: dict, resource_type: str, resource_id: str, changes: dict):
    await save_audit_log({
        'user_id': user['id'],
        'username': user['username'],
        'action': 'RESOURCE_UPDATED',
        'action_category': 'data_operation',
        'resource_type': resource_type,
        'resource_id': resource_id,
        'request_body': sanitize_data(changes)
    })

# 删除资源
async def log_resource_delete(user: dict, resource_type: str, resource_id: str):
    await save_audit_log({
        'user_id': user['id'],
        'username': user['username'],
        'action': 'RESOURCE_DELETED',
        'action_category': 'data_operation',
        'resource_type': resource_type,
        'resource_id': resource_id
    })
```

---

## 5. 审计日志查询 API

### 5.1 查询审计日志
```python
@app.get("/api/audit-logs")
@require_permission("system:admin")
async def query_audit_logs(
    request: Request,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    action_category: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    size: int = 20
):
    """
    查询审计日志
    """
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    
    if action:
        query += " AND action = %s"
        params.append(action)
    
    if action_category:
        query += " AND action_category = %s"
        params.append(action_category)
    
    if resource_type:
        query += " AND resource_type = %s"
        params.append(resource_type)
    
    if start_time:
        query += " AND action_time >= %s"
        params.append(start_time)
    
    if end_time:
        query += " AND action_time <= %s"
        params.append(end_time)
    
    query += " ORDER BY action_time DESC LIMIT %s OFFSET %s"
    params.extend([size, (page - 1) * size])
    
    logs = await db.fetch_all(query, params)
    
    return {
        "logs": logs,
        "page": page,
        "size": size,
        "total": await count_logs(params)
    }
```

### 5.2 导出审计日志
```python
@app.post("/api/audit-logs/export")
@require_permission("system:admin")
async def export_audit_logs(
    request: Request,
    filters: AuditLogFilters,
    format: str = "csv"
):
    """
    导出审计日志
    """
    logs = await query_logs(filters)
    
    if format == "csv":
        return generate_csv(logs)
    elif format == "json":
        return generate_json(logs)
    else:
        raise HTTPException(status_code=400, detail="不支持的格式")
```

---

## 6. 实施工作量

| 任务 | 工时 | 说明 |
|------|------|------|
| 数据库表设计 | 1 小时 | audit_logs 表 + 索引 |
| 审计中间件 | 2 小时 | 请求/响应记录 |
| 审计事件记录 | 2 小时 | 认证/授权/数据操作 |
| 查询 API | 1 小时 | 查询 + 导出 |
| 测试 | 1 小时 | 单元测试 |
| **总计** | **7 小时** | 约 1 个工作日 |

---

## 7. 验收标准

- [ ] 所有操作都有审计日志记录
- [ ] 日志包含完整的请求/响应信息
- [ ] 敏感信息已脱敏
- [ ] 查询 API 正常工作
- [ ] 日志分区正常
- [ ] 自动清理机制有效
- [ ] 性能影响<5%

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：已实施*
