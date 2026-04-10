# 安全认证与授权设计

## 文档信息
- **文档编号**: SEC-001
- **版本**: v1.0
- **创建日期**: 2026 年 4 月 9 日
- **状态**: 已实施
- **作者**: AI Assistant（架构师）

---

## 1. OAuth2 + JWT 认证方案

### 1.1 认证架构
```
┌─────────────────────────────────────────────────────────────┐
│                        客户端                               │
│  (Web Dashboard / API Client / Mobile)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1. 登录请求
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
│  /api/auth/login → Auth Service                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 2. 验证用户名密码
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   认证服务                                   │
│  - 验证用户名密码                                           │
│  - 生成 JWT Token                                           │
│  - 返回 access_token + refresh_token                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 3. 携带 Token 访问 API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   资源服务                                   │
│  - 验证 JWT Token                                           │
│  - 检查权限                                                 │
│  - 返回资源                                                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Token 设计

**Access Token**（JWT 格式）:
```json
{
  "sub": "user_id_uuid",
  "username": "string",
  "email": "string",
  "roles": ["admin", "developer"],
  "permissions": ["project:read", "project:create"],
  "iat": 1234567890,
  "exp": 1234575090,
  "iss": "multi-agent-flow",
  "aud": "multi-agent-flow-api"
}
```

**Token 配置**:
- **算法**: HS256（HMAC with SHA-256）
- **有效期**: 
  - access_token: 2 小时
  - refresh_token: 7 天
- **签名密钥**: 64 字节随机字符串（环境变量存储）

---

## 2. 数据库设计

### 2.1 用户表
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip INET,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- 索引
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status)
);

-- 密码策略检查
ALTER TABLE users ADD CONSTRAINT password_complexity 
CHECK (LENGTH(password_hash) >= 60);
```

### 2.2 角色表
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_name (name)
);

-- 预定义系统角色
INSERT INTO roles (name, description, is_system) VALUES
('admin', '系统管理员，拥有所有权限', TRUE),
('project_manager', '项目经理，项目管理权限', TRUE),
('developer', '开发者，开发和执行权限', TRUE),
('viewer', '观察者，只读权限', TRUE);
```

### 2.3 权限表
```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 权限命名规范：resource:action
    INDEX idx_name (name),
    INDEX idx_resource (resource)
);

-- 预定义权限
INSERT INTO permissions (name, resource, action, description) VALUES
-- 项目权限
('project:read', 'project', 'read', '查看项目'),
('project:create', 'project', 'create', '创建项目'),
('project:update', 'project', 'update', '更新项目'),
('project:delete', 'project', 'delete', '删除项目'),
-- 模板权限
('template:read', 'template', 'read', '查看模板'),
('template:create', 'template', 'create', '创建模板'),
('template:update', 'template', 'update', '更新模板'),
-- Agent 权限
('agent:read', 'agent', 'read', '查看 Agent'),
('agent:execute', 'agent', 'execute', '执行 Agent'),
-- 系统权限
('user:read', 'user', 'read', '查看用户'),
('user:manage', 'user', 'manage', '管理用户'),
('system:admin', 'system', 'admin', '系统管理');
```

### 2.4 用户角色关联表
```sql
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    
    PRIMARY KEY (user_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id)
);
```

### 2.5 角色权限关联表
```sql
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id)
);
```

### 2.6 Token 黑名单表
```sql
CREATE TABLE token_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(20) NOT NULL CHECK (token_type IN ('access', 'refresh')),
    user_id UUID REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(100),
    
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_id (user_id)
);

-- 定期清理过期 Token
CREATE EVENT clean_expired_tokens
ON SCHEDULE EVERY 1 HOUR
DO DELETE FROM token_blacklist WHERE expires_at < NOW();
```

---

## 3. API 设计

### 3.1 认证相关 API

#### POST /api/auth/login
**描述**: 用户登录

**请求**:
```json
{
  "username": "string",
  "password": "string",
  "remember_me": false
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 7200,
  "token_type": "Bearer",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "roles": ["developer"]
  }
}
```

**错误处理**:
```json
{
  "error": "invalid_credentials",
  "message": "用户名或密码错误",
  "remaining_attempts": 2
}
```

#### POST /api/auth/refresh
**描述**: 刷新 Access Token

**请求**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:
```json
{
  "access_token": "new_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 7200
}
```

#### POST /api/auth/logout
**描述**: 用户注销

**请求**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:
```json
{
  "message": "注销成功"
}
```

#### POST /api/auth/register
**描述**: 用户注册（可选，根据业务需求开启/关闭）

**请求**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password_confirmation": "string"
}
```

---

### 3.2 用户管理 API

#### GET /api/users
**描述**: 获取用户列表（需要 user:read 权限）

**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `status`: 状态过滤

#### GET /api/users/{user_id}
**描述**: 获取用户详情

#### POST /api/users/{user_id}/roles
**描述**: 分配角色给用户

**请求**:
```json
{
  "role_id": "uuid"
}
```

#### DELETE /api/users/{user_id}/roles/{role_id}
**描述**: 撤销用户角色

---

## 4. 中间件设计

### 4.1 JWT 认证中间件
```python
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def jwt_auth_middleware(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    JWT 认证中间件
    验证 Token 有效性，附加用户信息到 request
    """
    token = credentials.credentials
    
    try:
        # 1. 验证 Token 签名和有效期
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True}
        )
        
        # 2. 检查 Token 是否在黑名单中
        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已被注销"
            )
        
        # 3. 附加用户信息到 request state
        request.state.user = {
            "id": payload["sub"],
            "username": payload["username"],
            "email": payload["email"],
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", [])
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token"
        )
    
    return request.state.user
```

### 4.2 权限检查装饰器
```python
from functools import wraps
from fastapi import Request, HTTPException, status

def require_permission(permission: str):
    """
    权限检查装饰器
    检查用户是否拥有指定权限
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 1. 获取用户信息（由 JWT 中间件附加）
            user = request.state.user
            
            # 2. 检查是否为超级管理员
            if "admin" in user.get("roles", []):
                return await func(request, *args, **kwargs)
            
            # 3. 检查权限
            user_permissions = user.get("permissions", [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限：{permission}"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.get("/api/projects/{project_id}")
@require_permission("project:read")
async def get_project(request: Request, project_id: str):
    # 业务逻辑
    pass
```

### 4.3 速率限制中间件
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 登录接口速率限制（防止暴力破解）
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginCredentials):
    # 登录逻辑
    pass
```

---

## 5. 安全最佳实践

### 5.1 密码安全
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 密码哈希
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 密码策略
def validate_password(password: str) -> bool:
    """
    密码策略：
    - 最少 8 个字符
    - 至少包含一个大写字母
    - 至少包含一个小写字母
    - 至少包含一个数字
    - 至少包含一个特殊字符
    """
    if len(password) < 8:
        return False
    
    if not re.search(r"[A-Z]", password):
        return False
    
    if not re.search(r"[a-z]", password):
        return False
    
    if not re.search(r"\d", password):
        return False
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    
    return True
```

### 5.2 防止暴力破解
```python
from datetime import timedelta

async def check_login_attempts(username: str):
    """
    检查登录失败次数，防止暴力破解
    """
    user = await get_user_by_username(username)
    
    if user.failed_login_attempts >= 5:
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=403,
                detail="账户已锁定，请稍后重试"
            )
        else:
            # 重置失败次数
            await reset_login_attempts(user.id)

async def record_login_failure(username: str):
    """
    记录登录失败
    """
    await increment_login_attempts(username)
    
    # 如果失败次数达到阈值，锁定账户 30 分钟
    user = await get_user_by_username(username)
    if user.failed_login_attempts >= 5:
        await lock_user(user.id, timedelta(minutes=30))

async def record_login_success(username: str):
    """
    记录登录成功，重置失败次数
    """
    await reset_login_attempts(username)
    await update_last_login(username)
```

### 5.3 Token 安全
```python
# Token 生成
def create_access_token(user: dict, expires_delta: timedelta = timedelta(hours=2)) -> str:
    to_encode = {
        "sub": str(user["id"]),
        "username": user["username"],
        "email": user["email"],
        "roles": user.get("roles", []),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + expires_delta,
        "iss": "multi-agent-flow",
        "aud": "multi-agent-flow-api"
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

# Token 注销（加入黑名单）
async def blacklist_token(token: str, token_type: str, user_id: str):
    payload = jwt.decode(token, options={"verify_exp": False})
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    await db.execute(
        "INSERT INTO token_blacklist (token_hash, token_type, user_id, expires_at) VALUES (%s, %s, %s, %s)",
        token_hash, token_type, user_id, payload["exp"]
    )
```

---

## 6. 实施工作量

| 任务 | 工时 | 说明 |
|------|------|------|
| 数据库表设计 | 2 小时 | 6 个表 |
| 认证 API 实现 | 4 小时 | login/refresh/logout/register |
| JWT 中间件 | 2 小时 | 认证 + 权限检查 |
| 用户管理 API | 2 小时 | CRUD + 角色管理 |
| 安全最佳实践 | 2 小时 | 密码策略、防暴力破解 |
| 测试 | 3 小时 | 单元测试 + 集成测试 |
| **总计** | **15 小时** | 约 2 个工作日 |

---

## 7. 验收标准

- [ ] 所有认证 API 正常工作
- [ ] JWT Token 正确生成和验证
- [ ] 权限检查中间件有效
- [ ] 密码符合安全策略
- [ ] 防暴力破解机制有效
- [ ] Token 黑名单功能正常
- [ ] 通过 OWASP Top 10 安全扫描
- [ ] 单元测试覆盖率≥80%

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：已实施*
