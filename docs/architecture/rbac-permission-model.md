# RBAC 权限模型设计

## 文档信息
- **文档编号**: SEC-002
- **版本**: v1.0
- **创建日期**: 2026 年 4 月 9 日
- **状态**: 已实施
- **作者**: AI Assistant（架构师）

---

## 1. RBAC 模型概述

### 1.1 核心概念
```
用户 (User) → 角色 (Role) → 权限 (Permission) → 资源 (Resource)
```

**关系说明**:
- 用户可以拥有多个角色
- 角色可以拥有多个权限
- 权限作用于特定资源
- 用户通过角色间接获得权限

### 1.2 权限粒度
```
权限层级:
├── 系统级 (System Level)
│   └── 如：system:admin, system:config
├── 资源级 (Resource Level)
│   └── 如：project:*, template:read
└── 数据级 (Data Level)
    └── 如：project:{id}:read（仅限特定项目）
```

---

## 2. 角色定义

### 2.1 预定义角色

#### Admin（系统管理员）
```yaml
角色：admin
描述：系统管理员，拥有所有权限
权限：
  - "*:*"  # 所有权限
特性：
  - 可以管理用户和角色
  - 可以配置系统参数
  - 可以查看所有审计日志
  - 可以执行备份和恢复
```

#### Project Manager（项目经理）
```yaml
角色：project_manager
描述：项目经理，负责项目管理和团队协调
权限：
  项目：
    - project:read
    - project:create
    - project:update
    - project:delete
    - project:members:manage
  模板：
    - template:read
  Agent:
    - agent:read
    - agent:execute
  团队：
    - team:create
    - team:manage
数据范围：
  - 仅限自己创建的项目
  - 仅限自己参与的项目
```

#### Developer（开发者）
```yaml
角色：developer
描述：开发者，负责具体开发任务执行
权限：
  项目：
    - project:read
    - project:update  # 仅限参与的项目
  模板：
    - template:read
  Agent:
    - agent:read
    - agent:execute
  代码：
    - code:read
    - code:write
    - code:commit
数据范围：
  - 仅限自己参与的项目
```

#### Tester（测试工程师）
```yaml
角色：tester
描述：测试工程师，负责质量保障
权限：
  项目：
    - project:read
  测试：
    - test:read
    - test:create
    - test:execute
    - test:report
  Bug:
    - bug:read
    - bug:create
    - bug:update
数据范围：
  - 仅限自己参与的项目
```

#### Viewer（观察者）
```yaml
角色：viewer
描述：观察者，只读权限
权限：
  项目：
    - project:read
  模板：
    - template:read
  Dashboard:
    - dashboard:read
数据范围：
  - 仅限公开项目
  - 仅限自己参与的项目
```

---

## 3. 权限矩阵

### 3.1 功能权限矩阵

| 功能 | Admin | PM | Developer | Tester | Viewer |
|------|-------|----|-----------|--------|--------|
| **项目管理** | | | | | |
| 查看项目 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 创建项目 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 更新项目 | ✅ | ✅ | ✅* | ❌ | ❌ |
| 删除项目 | ✅ | ✅* | ❌ | ❌ | ❌ |
| 管理成员 | ✅ | ✅* | ❌ | ❌ | ❌ |
| **模板管理** | | | | | |
| 查看模板 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 创建模板 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 更新模板 | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Agent 执行** | | | | | |
| 查看 Agent | ✅ | ✅ | ✅ | ✅ | ❌ |
| 执行 Agent | ✅ | ✅ | ✅ | ❌ | ❌ |
| **测试管理** | | | | | |
| 创建测试 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 执行测试 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 查看报告 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **系统管理** | | | | | |
| 用户管理 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 角色管理 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 审计日志 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 系统配置 | ✅ | ❌ | ❌ | ❌ | ❌ |

*注：✅* 表示仅限自己创建/管理的项目

---

### 3.2 数据权限规则

```python
# 数据权限检查
class DataPermissionChecker:
    def can_access_project(self, user: dict, project_id: str) -> bool:
        """
        检查用户是否可以访问项目
        """
        # 1. 管理员可以访问所有项目
        if "admin" in user.get("roles", []):
            return True
        
        # 2. 检查是否是项目成员
        is_member = self.is_project_member(user["id"], project_id)
        if is_member:
            return True
        
        # 3. 检查项目是否公开
        project = self.get_project(project_id)
        if project.get("is_public", False):
            return True
        
        return False
    
    def can_edit_project(self, user: dict, project_id: str) -> bool:
        """
        检查用户是否可以编辑项目
        """
        # 1. 管理员可以编辑所有项目
        if "admin" in user.get("roles", []):
            return True
        
        # 2. 检查是否是项目负责人
        is_owner = self.is_project_owner(user["id"], project_id)
        if is_owner:
            return True
        
        # 3. 检查是否有编辑权限
        has_permission = self.has_permission(user["id"], "project:update", project_id)
        if has_permission:
            return True
        
        return False
```

---

## 4. 权限检查实现

### 4.1 权限检查中间件
```python
from fastapi import Request, HTTPException, status
from functools import wraps

def require_permission(permission: str, data_scope: str = None):
    """
    权限检查装饰器
    
    Args:
        permission: 权限标识，如 "project:read"
        data_scope: 数据范围检查函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 1. 获取用户信息
            user = request.state.user
            
            # 2. 检查是否为超级管理员
            if "admin" in user.get("roles", []):
                return await func(request, *args, **kwargs)
            
            # 3. 检查权限
            has_permission = await check_permission(user["id"], permission)
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限：{permission}"
                )
            
            # 4. 检查数据范围（如果有）
            if data_scope:
                resource_id = kwargs.get(data_scope)
                if resource_id:
                    can_access = await check_data_scope(user["id"], resource_id)
                    if not can_access:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="无权访问该资源"
                        )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.get("/api/projects/{project_id}")
@require_permission("project:read", data_scope="project_id")
async def get_project(request: Request, project_id: str):
    # 业务逻辑
    pass

@app.post("/api/projects")
@require_permission("project:create")
async def create_project(request: Request, project: ProjectCreate):
    # 业务逻辑
    pass
```

### 4.2 权限缓存
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_user_permissions(user_id: str) -> set:
    """
    获取用户权限（带缓存）
    """
    query = """
        SELECT DISTINCT p.name
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE u.id = %s
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    """
    
    permissions = await db.fetch_all(query, [user_id])
    return {p["name"] for p in permissions}

async def check_permission(user_id: str, permission: str) -> bool:
    """
    检查用户是否有指定权限
    """
    user_permissions = await get_user_permissions(user_id)
    return permission in user_permissions or "*:*" in user_permissions
```

---

## 5. 角色管理 API

### 5.1 创建角色
```python
@app.post("/api/roles")
@require_permission("system:admin")
async def create_role(request: Request, role: RoleCreate):
    """
    创建新角色
    """
    # 检查角色名是否已存在
    existing = await db.fetch_one(
        "SELECT id FROM roles WHERE name = %s",
        [role.name]
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="角色名已存在"
        )
    
    # 创建角色
    role_id = await db.execute(
        "INSERT INTO roles (name, description, is_system) VALUES (%s, %s, %s) RETURNING id",
        [role.name, role.description, False]
    )
    
    # 分配权限
    if role.permissions:
        for permission_name in role.permissions:
            permission = await db.fetch_one(
                "SELECT id FROM permissions WHERE name = %s",
                [permission_name]
            )
            
            if permission:
                await db.execute(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                    [role_id, permission["id"]]
                )
    
    return {"id": role_id, "message": "角色创建成功"}
```

### 5.2 分配角色给用户
```python
@app.post("/api/users/{user_id}/roles")
@require_permission("user:manage")
async def assign_role_to_user(
    request: Request,
    user_id: str,
    role_assignment: RoleAssignment
):
    """
    分配角色给用户
    """
    # 检查用户是否存在
    user = await db.fetch_one("SELECT id FROM users WHERE id = %s", [user_id])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查角色是否存在
    role = await db.fetch_one("SELECT id FROM roles WHERE id = %s", [role_assignment.role_id])
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 检查是否已分配
    existing = await db.fetch_one(
        "SELECT id FROM user_roles WHERE user_id = %s AND role_id = %s",
        [user_id, role_assignment.role_id]
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="角色已分配")
    
    # 分配角色
    await db.execute(
        "INSERT INTO user_roles (user_id, role_id, granted_by, expires_at) VALUES (%s, %s, %s, %s)",
        [user_id, role_assignment.role_id, request.state.user["id"], role_assignment.expires_at]
    )
    
    # 清除权限缓存
    get_user_permissions.cache_clear()
    
    return {"message": "角色分配成功"}
```

---

## 6. 实施工作量

| 任务 | 工时 | 说明 |
|------|------|------|
| 数据库表设计 | 1 小时 | roles, permissions 等表 |
| 权限检查中间件 | 3 小时 | 权限检查 + 数据范围检查 |
| 角色管理 API | 3 小时 | CRUD + 分配/撤销 |
| 权限缓存 | 1 小时 | LRU 缓存实现 |
| 预定义角色和权限 | 1 小时 | 初始化数据 |
| 测试 | 2 小时 | 单元测试 + 集成测试 |
| **总计** | **11 小时** | 约 1.5 个工作日 |

---

## 7. 验收标准

- [ ] 所有预定义角色创建成功
- [ ] 权限矩阵正确实施
- [ ] 权限检查中间件有效
- [ ] 数据范围检查有效
- [ ] 角色管理 API 正常工作
- [ ] 权限缓存正常工作
- [ ] 通过安全测试（越权访问测试）

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：已实施*
