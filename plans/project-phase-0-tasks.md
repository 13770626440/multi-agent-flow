# 阶段 0：安全整改 - 详细任务表

## 阶段信息
- **阶段名称**: 安全整改
- **工期**: 1 周（2026-04-10 至 04-17）
- **目标**: 完成 P0/P1 问题整改，通过安全扫描
- **总任务数**: 24 个任务
- **单任务时长**: ≤15 分钟

---

## 阶段 0-1：认证 + 权限实施（04-10 至 04-13）

### 任务 1: 创建 users 表
**任务 ID**: SEC-001-T01
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- 数据库连接（PostgreSQL）
- 设计文档：security-authentication-design.md

**执行步骤**:
1. 执行 SQL 创建 users 表
2. 创建索引（username, email, status）
3. 验证表结构

**输出**:
- users 表创建成功
- 索引创建成功

**验证方法**:
```sql
\d users  -- 查看表结构
\di       -- 查看索引
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS users CASCADE;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 索引创建成功
- [ ] 可以插入测试数据

---

### 任务 2: 创建 roles 表
**任务 ID**: SEC-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- users 表已创建
- 设计文档

**执行步骤**:
1. 执行 SQL 创建 roles 表
2. 创建索引（name）
3. 插入预定义角色（admin, pm, developer, tester, viewer）

**输出**:
- roles 表创建成功
- 5 个预定义角色数据

**验证方法**:
```sql
SELECT * FROM roles;
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS roles CASCADE;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 5 个预定义角色已插入

---

### 任务 3: 创建 permissions 表
**任务 ID**: SEC-001-T03
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- roles 表已创建
- 权限列表

**执行步骤**:
1. 执行 SQL 创建 permissions 表
2. 创建索引（name, resource）
3. 插入预定义权限（20+ 权限）

**输出**:
- permissions 表创建成功
- 预定义权限数据

**验证方法**:
```sql
SELECT * FROM permissions WHERE resource = 'project';
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS permissions CASCADE;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 至少 20 个权限已插入

---

### 任务 4: 创建 user_roles 表
**任务 ID**: SEC-001-T04
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- users 表已创建
- roles 表已创建

**执行步骤**:
1. 执行 SQL 创建 user_roles 表（复合主键）
2. 创建外键约束
3. 创建索引（user_id, role_id）

**输出**:
- user_roles 表创建成功
- 外键约束生效

**验证方法**:
```sql
\d user_roles  -- 查看表结构和约束
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS user_roles;
```

**验收标准**:
- [ ] 复合主键正确
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### 任务 5: 创建 role_permissions 表
**任务 ID**: SEC-001-T05
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- roles 表已创建
- permissions 表已创建

**执行步骤**:
1. 执行 SQL 创建 role_permissions 表
2. 创建外键约束
3. 创建索引（role_id, permission_id）

**输出**:
- role_permissions 表创建成功

**验证方法**:
```sql
\d role_permissions
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS role_permissions;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 外键约束生效

---

### 任务 6: 创建 token_blacklist 表
**任务 ID**: SEC-001-T06
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- 设计文档

**执行步骤**:
1. 执行 SQL 创建 token_blacklist 表
2. 创建索引（token_hash, expires_at, user_id）
3. 创建定时清理事件

**输出**:
- token_blacklist 表创建成功
- 定时清理事件创建成功

**验证方法**:
```sql
\d token_blacklist
SELECT * FROM pg_cron.job;  -- 查看定时任务
```

**回滚方案**:
```sql
DROP TABLE IF EXISTS token_blacklist;
```

**验收标准**:
- [ ] 表结构符合设计
- [ ] 索引创建成功
- [ ] 定时清理事件创建成功

---

### 任务 7: 实现密码哈希函数
**任务 ID**: SEC-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Python 环境
- bcrypt 库

**执行步骤**:
1. 安装 bcrypt 库：`pip install bcrypt`
2. 创建 utils/password.py
3. 实现 hash_password 函数
4. 实现 verify_password 函数
5. 实现 validate_password 函数

**输出**:
- utils/password.py 文件
- 3 个函数可正常调用

**验证方法**:
```python
from utils.password import hash_password, verify_password
hashed = hash_password("Test123!@#")
assert verify_password("Test123!@#", hashed) == True
```

**回滚方案**:
```bash
rm utils/password.py
```

**验收标准**:
- [ ] hash_password 返回 bcrypt 哈希
- [ ] verify_password 验证正确
- [ ] validate_password 检查密码策略

---

### 任务 8: 实现 JWT Token 生成
**任务 ID**: SEC-001-T08
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Python 环境
- PyJWT 库

**执行步骤**:
1. 安装 PyJWT：`pip install pyjwt`
2. 创建 utils/jwt.py
3. 实现 create_access_token 函数
4. 实现 create_refresh_token 函数
5. 设置 JWT_SECRET_KEY 环境变量

**输出**:
- utils/jwt.py 文件
- 2 个 Token 生成函数

**验证方法**:
```python
from utils.jwt import create_access_token
token = create_access_token({"id": "uuid", "username": "test"})
assert token is not None
```

**回滚方案**:
```bash
rm utils/jwt.py
```

**验收标准**:
- [ ] access_token 生成正确
- [ ] refresh_token 生成正确
- [ ] Token 包含必需字段（sub, exp, iat）

---

### 任务 9: 实现 JWT Token 验证
**任务 ID**: SEC-001-T09
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- utils/jwt.py 已创建

**执行步骤**:
1. 实现 verify_token 函数
2. 实现 decode_token 函数
3. 处理 ExpiredSignatureError
4. 处理 InvalidTokenError

**输出**:
- verify_token 函数
- decode_token 函数

**验证方法**:
```python
from utils.jwt import verify_token, create_access_token
token = create_access_token({"id": "uuid"})
payload = verify_token(token)
assert payload["sub"] == "uuid"
```

**回滚方案**:
```bash
# 回滚到上一个版本
git checkout HEAD~1 utils/jwt.py
```

**验收标准**:
- [ ] 有效 Token 验证通过
- [ ] 过期 Token 抛出异常
- [ ] 无效 Token 抛出异常

---

### 任务 10: 实现 Token 黑名单检查
**任务 ID**: SEC-001-T10
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- token_blacklist 表已创建
- utils/jwt.py 已创建

**执行步骤**:
1. 实现 is_token_blacklisted 函数
2. 实现 blacklist_token 函数
3. 数据库连接配置

**输出**:
- is_token_blacklisted 函数
- blacklist_token 函数

**验证方法**:
```python
from utils.jwt import blacklist_token, is_token_blacklisted
blacklist_token("token123", "access", "uuid")
assert is_token_blacklisted("token123") == True
```

**回滚方案**:
```bash
# 回滚 JWT 模块
git checkout HEAD~1 utils/jwt.py
```

**验收标准**:
- [ ] 黑名单检查正确
- [ ] Token 可以加入黑名单

---

### 任务 11: 实现登录 API
**任务 ID**: SEC-001-T11
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- FastAPI 环境
- utils/password.py, utils/jwt.py 已完成

**执行步骤**:
1. 创建 api/auth.py
2. 实现 POST /api/auth/login 端点
3. 实现用户名密码验证
4. 实现登录失败次数限制
5. 返回 access_token + refresh_token

**输出**:
- POST /api/auth/login 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**回滚方案**:
```bash
rm api/auth.py
```

**验收标准**:
- [ ] 登录成功返回 Token
- [ ] 登录失败返回错误
- [ ] 失败次数限制有效

---

### 任务 12: 实现刷新 Token API
**任务 ID**: SEC-001-T12
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- api/auth.py 已创建

**执行步骤**:
1. 实现 POST /api/auth/refresh 端点
2. 验证 refresh_token
3. 生成新的 access_token

**输出**:
- POST /api/auth/refresh 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"..."}'
```

**回滚方案**:
```bash
# 注释掉 refresh 端点
```

**验收标准**:
- [ ] 刷新成功返回新 Token
- [ ] 无效 refresh_token 返回错误

---

### 任务 13: 实现注销 API
**任务 ID**: SEC-001-T13
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- api/auth.py 已创建

**执行步骤**:
1. 实现 POST /api/auth/logout 端点
2. 将 Token 加入黑名单
3. 清理客户端 Cookie

**输出**:
- POST /api/auth/logout 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer TOKEN"
```

**回滚方案**:
```bash
# 注释掉 logout 端点
```

**验收标准**:
- [ ] 注销成功
- [ ] Token 加入黑名单

---

### 任务 14: 实现 JWT 认证中间件
**任务 ID**: SEC-001-T14
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- FastAPI 环境
- utils/jwt.py 已完成

**执行步骤**:
1. 创建 middleware/auth.py
2. 实现 jwt_auth_middleware 函数
3. 实现 HTTPBearer
4. 附加用户信息到 request.state

**输出**:
- middleware/auth.py 文件
- jwt_auth_middleware 函数

**验证方法**:
```python
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get("/api/protected", headers={"Authorization": "Bearer TOKEN"})
assert response.status_code == 200
```

**回滚方案**:
```bash
rm middleware/auth.py
```

**验收标准**:
- [ ] 有效 Token 通过
- [ ] 无效 Token 拒绝
- [ ] 用户信息附加到 request

---

### 任务 15: 实现权限检查装饰器
**任务 ID**: SEC-001-T15
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- middleware/auth.py 已创建

**执行步骤**:
1. 创建 decorators/permissions.py
2. 实现 require_permission 装饰器
3. 实现 check_permission 函数
4. 实现管理员豁免逻辑

**输出**:
- decorators/permissions.py 文件
- require_permission 装饰器

**验证方法**:
```python
@app.get("/api/projects")
@require_permission("project:read")
async def get_projects():
    pass

# 测试无权限访问
response = client.get("/api/projects", headers={"Authorization": "Bearer TOKEN"})
assert response.status_code == 403
```

**回滚方案**:
```bash
rm decorators/permissions.py
```

**验收标准**:
- [ ] 有权限访问成功
- [ ] 无权限返回 403
- [ ] 管理员豁免生效

---

### 任务 16: 实现数据范围检查
**任务 ID**: SEC-001-T16
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- decorators/permissions.py 已创建

**执行步骤**:
1. 实现 check_data_scope 函数
2. 实现 is_project_member 函数
3. 实现 is_project_owner 函数

**输出**:
- check_data_scope 函数
- is_project_member 函数
- is_project_owner 函数

**验证方法**:
```python
assert check_data_scope("user_id", "project_id") == True
```

**回滚方案**:
```bash
# 回滚 decorators/permissions.py
git checkout HEAD~1 decorators/permissions.py
```

**验收标准**:
- [ ] 项目成员检查正确
- [ ] 项目所有者检查正确
- [ ] 数据范围限制生效

---

### 任务 17: 实现防暴力破解
**任务 ID**: SEC-001-T17
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- users 表已创建

**执行步骤**:
1. 实现 check_login_attempts 函数
2. 实现 record_login_failure 函数
3. 实现 record_login_success 函数
4. 实现账户锁定逻辑

**输出**:
- 防暴力破解函数
- 账户锁定功能

**验证方法**:
```python
# 连续失败 5 次
for i in range(5):
    record_login_failure("testuser")
# 第 6 次应该被锁定
assert check_login_attempts("testuser") == False
```

**回滚方案**:
```bash
# 回滚相关函数
```

**验收标准**:
- [ ] 失败 5 次后账户锁定
- [ ] 锁定 30 分钟后自动解锁
- [ ] 登录成功重置失败次数

---

### 任务 18: 实现速率限制
**任务 ID**: SEC-001-T18
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- FastAPI 环境

**执行步骤**:
1. 安装 slowapi：`pip install slowapi`
2. 配置 Limiter
3. 为登录接口添加速率限制（5 次/分钟）

**输出**:
- 速率限制中间件
- 登录接口限流

**验证方法**:
```bash
# 连续请求 6 次
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login ...
done
# 第 6 次应该返回 429
```

**回滚方案**:
```bash
# 移除 slowapi 配置
```

**验收标准**:
- [ ] 登录接口限流生效
- [ ] 超过限制返回 429

---

### 任务 19: 实现用户注册 API（可选）
**任务 ID**: SEC-001-T19
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- api/auth.py 已创建

**执行步骤**:
1. 实现 POST /api/auth/register 端点
2. 验证密码策略
3. 检查用户名/邮箱唯一性
4. 哈希密码并存储

**输出**:
- POST /api/auth/register 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"new@test.com","password":"Test123!@#"}'
```

**回滚方案**:
```bash
# 注释掉 register 端点
```

**验收标准**:
- [ ] 注册成功创建用户
- [ ] 重复用户名返回错误
- [ ] 弱密码返回错误

---

### 任务 20: 实现角色管理 API
**任务 ID**: SEC-001-T20
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- roles 表已创建
- permissions 表已创建

**执行步骤**:
1. 创建 api/roles.py
2. 实现 GET /api/roles 端点
3. 实现 POST /api/roles 端点
4. 实现 POST /api/users/{user_id}/roles 端点

**输出**:
- 角色管理 API 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/users/uuid/roles \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"role_id":"uuid"}'
```

**回滚方案**:
```bash
rm api/roles.py
```

**验收标准**:
- [ ] 角色列表查询成功
- [ ] 角色创建成功
- [ ] 角色分配成功

---

### 任务 21: 实现权限缓存
**任务 ID**: SEC-001-T21
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- decorators/permissions.py 已创建

**执行步骤**:
1. 安装 cachetools：`pip install cachetools`
2. 实现 get_user_permissions 函数（带 LRU 缓存）
3. 实现缓存清除机制

**输出**:
- get_user_permissions 函数（缓存版）

**验证方法**:
```python
from decorators.permissions import get_user_permissions
# 第一次查询（慢）
perms1 = await get_user_permissions("user_id")
# 第二次查询（快，从缓存）
perms2 = await get_user_permissions("user_id")
assert perms1 == perms2
```

**回滚方案**:
```bash
# 移除缓存装饰器
```

**验收标准**:
- [ ] 权限查询有缓存
- [ ] 缓存命中率>80%
- [ ] 缓存清除生效

---

### 任务 22: 编写认证单元测试
**任务 ID**: SEC-001-T22
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有认证代码已完成

**执行步骤**:
1. 创建 tests/test_auth.py
2. 编写登录测试
3. 编写 Token 验证测试
4. 编写权限检查测试
5. 运行测试

**输出**:
- tests/test_auth.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_auth.py -v
```

**回滚方案**:
```bash
rm tests/test_auth.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

### 任务 23: 编写权限单元测试
**任务 ID**: SEC-001-T23
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有权限代码已完成

**执行步骤**:
1. 创建 tests/test_permissions.py
2. 编写角色管理测试
3. 编写数据范围测试
4. 运行测试

**输出**:
- tests/test_permissions.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_permissions.py -v
```

**回滚方案**:
```bash
rm tests/test_permissions.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

### 任务 24: 安全扫描
**任务 ID**: SEC-001-T24
**预计时长**: 15 分钟
**负责人**: 架构师

**输入**:
- 所有认证权限代码已完成

**执行步骤**:
1. 安装安全扫描工具：`pip install bandit safety`
2. 运行 bandit 扫描：`bandit -r .`
3. 运行 safety 扫描：`safety check`
4. 修复发现的漏洞

**输出**:
- 安全扫描报告
- 漏洞修复记录

**验证方法**:
```bash
bandit -r . && safety check
```

**回滚方案**:
```bash
# 不适用
```

**验收标准**:
- [ ] 无 P0/P1 安全漏洞
- [ ] 所有建议已处理

---

## 阶段 0-1 总结

**总任务数**: 24 个
**总工时**: 6 小时（24 × 15 分钟）
**完成率**: 0/24

**关键路径**:
1. 数据库表创建（T01-T06）
2. 密码和 JWT 实现（T07-T10）
3. 认证 API（T11-T13）
4. 中间件和装饰器（T14-T16）
5. 安全加固（T17-T21）
6. 测试和扫描（T22-T24）

**依赖关系**:
```
T01 → T02 → T03 → T04 → T05 → T06
                          ↓
T07 → T08 → T09 → T10 → T11 → T12 → T13
                          ↓
                    T14 → T15 → T16
                          ↓
                    T17 → T18 → T19 → T20 → T21
                          ↓
                    T22 → T23 → T24
```

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：待执行*
