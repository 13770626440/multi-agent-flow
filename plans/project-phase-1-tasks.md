# 阶段一：基础架构 - 详细任务表

## 阶段信息
- **阶段名称**: 基础架构
- **工期**: 2 周（2026-04-18 至 05-01）
- **目标**: OpenMOSS Dashboard 集成，基础 API 集成层，简化模板系统，TODO 应用演示
- **总任务数**: 36 个
- **单任务时长**: ≤15 分钟

---

## 阶段一 -1：环境搭建与 OpenMOSS 部署（第 1 周，04-18 至 04-24）

### 任务 1: 安装 Docker Desktop
**任务 ID**: ENV-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Windows 10/11 操作系统
- 管理员权限

**执行步骤**:
1. 下载 Docker Desktop：https://www.docker.com/products/docker-desktop
2. 运行安装程序
3. 按照向导完成安装
4. 启动 Docker Desktop
5. 验证安装

**输出**:
- Docker Desktop 安装成功
- Docker 服务运行正常

**验证方法**:
```bash
docker --version
docker-compose --version
```

**回滚方案**:
```bash
# 卸载 Docker Desktop
# 控制面板 → 程序 → 卸载程序 → Docker Desktop
```

**验收标准**:
- [ ] Docker 版本显示正常
- [ ] Docker Compose 版本显示正常
- [ ] Docker 服务运行正常

---

### 任务 2: 克隆项目代码
**任务 ID**: ENV-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- Git 已安装
- 项目仓库地址

**执行步骤**:
1. 打开 PowerShell
2. 切换到 D:\coding 目录
3. 克隆项目代码（如果有仓库）
4. 或者创建空项目结构

**输出**:
- D:\coding\multi-agent-flow 目录
- 项目基础结构

**验证方法**:
```bash
cd D:\coding\multi-agent-flow
dir
```

**回滚方案**:
```bash
# 删除项目目录
rmdir /s D:\coding\multi-agent-flow
```

**验收标准**:
- [ ] 项目目录创建成功
- [ ] 基础结构完整

---

### 任务 3: 创建 Docker Compose 配置文件
**任务 ID**: ENV-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Docker Desktop 已安装
- 项目目录已创建

**执行步骤**:
1. 创建 docker-compose.yml 文件
2. 定义 PostgreSQL 服务
3. 定义 Redis 服务
4. 定义 Qdrant 服务
5. 定义 OpenMOSS 服务

**输出**:
- docker-compose.yml 文件

**验证方法**:
```bash
cat docker-compose.yml
```

**回滚方案**:
```bash
rm docker-compose.yml
```

**验收标准**:
- [ ] YAML 格式正确
- [ ] 所有服务定义完整
- [ ] 网络和卷配置正确

---

### 任务 4: 创建环境变量配置
**任务 ID**: ENV-001-T04
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- docker-compose.yml 已创建

**执行步骤**:
1. 创建 .env 文件
2. 配置数据库密码
3. 配置 Redis 密码
4. 配置 OpenMOSS API Key
5. 配置其他环境变量

**输出**:
- .env 文件

**验证方法**:
```bash
cat .env
```

**回滚方案**:
```bash
rm .env
```

**验收标准**:
- [ ] 所有必需环境变量已配置
- [ ] 密码使用强密码
- [ ] .env 已加入.gitignore

---

### 任务 5: 启动 PostgreSQL 容器
**任务 ID**: ENV-001-T05
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- docker-compose.yml 已创建
- .env 文件已创建

**执行步骤**:
1. 执行 `docker-compose up -d postgres`
2. 等待容器启动
3. 验证 PostgreSQL 运行状态

**输出**:
- PostgreSQL 容器运行中

**验证方法**:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

**回滚方案**:
```bash
docker-compose down postgres
```

**验收标准**:
- [ ] 容器状态为 Up
- [ ] 无错误日志
- [ ] 可以连接数据库

---

### 任务 6: 启动 Redis 容器
**任务 ID**: ENV-001-T06
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- PostgreSQL 容器已启动

**执行步骤**:
1. 执行 `docker-compose up -d redis`
2. 等待容器启动
3. 验证 Redis 运行状态

**输出**:
- Redis 容器运行中

**验证方法**:
```bash
docker-compose ps redis
docker-compose exec redis redis-cli ping
```

**回滚方案**:
```bash
docker-compose down redis
```

**验收标准**:
- [ ] 容器状态为 Up
- [ ] PING 返回 PONG
- [ ] 无错误日志

---

### 任务 7: 启动 Qdrant 容器
**任务 ID**: ENV-001-T07
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- Redis 容器已启动

**执行步骤**:
1. 执行 `docker-compose up -d qdrant`
2. 等待容器启动
3. 验证 Qdrant 运行状态

**输出**:
- Qdrant 容器运行中

**验证方法**:
```bash
docker-compose ps qdrant
curl http://localhost:6333/
```

**回滚方案**:
```bash
docker-compose down qdrant
```

**验收标准**:
- [ ] 容器状态为 Up
- [ ] API 返回 OK
- [ ] 无错误日志

---

### 任务 8: 启动 OpenMOSS 容器
**任务 ID**: ENV-001-T08
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- PostgreSQL 容器已启动
- Qdrant 容器已启动

**执行步骤**:
1. 执行 `docker-compose up -d openmoss`
2. 等待容器启动（首次启动需要初始化数据库）
3. 验证 OpenMOSS 运行状态
4. 访问 Dashboard

**输出**:
- OpenMOSS 容器运行中
- Dashboard 可访问

**验证方法**:
```bash
docker-compose ps openmoss
curl http://localhost:6565/api/health
open http://localhost:6565/dashboard
```

**回滚方案**:
```bash
docker-compose down openmoss
```

**验收标准**:
- [ ] 容器状态为 Up
- [ ] Health 检查通过
- [ ] Dashboard 可访问

---

### 任务 9: 验证数据库连接
**任务 ID**: ENV-001-T09
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- PostgreSQL 容器已启动
- OpenMOSS 容器已启动

**执行步骤**:
1. 使用 psql 连接数据库
2. 查看 OpenMOSS 创建的表
3. 验证表结构

**输出**:
- 数据库连接成功
- 表结构验证通过

**验证方法**:
```bash
docker-compose exec postgres psql -U multiagent -d multiagent -c "\dt"
```

**回滚方案**:
```bash
# 检查数据库配置
docker-compose logs postgres
```

**验收标准**:
- [ ] 数据库连接成功
- [ ] OpenMOSS 表已创建
- [ ] 表结构正确

---

### 任务 10: 创建后端项目结构
**任务 ID**: ENV-001-T10
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 项目目录已创建

**执行步骤**:
1. 创建 code/backend 目录
2. 创建 main.py 文件
3. 创建 api/ 目录
4. 创建 services/ 目录
5. 创建 middleware/ 目录
6. 创建 requirements.txt 文件

**输出**:
- code/backend/ 目录结构
- requirements.txt 文件

**验证方法**:
```bash
tree code/backend
cat code/backend/requirements.txt
```

**回滚方案**:
```bash
rm -rf code/backend
```

**验收标准**:
- [ ] 目录结构完整
- [ ] requirements.txt 包含必需依赖
- [ ] main.py 包含 FastAPI 基础代码

---

### 任务 11: 安装 Python 依赖
**任务 ID**: ENV-001-T11
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- requirements.txt 已创建
- Python 3.11+ 已安装

**执行步骤**:
1. 创建虚拟环境：`python -m venv venv`
2. 激活虚拟环境
3. 安装依赖：`pip install -r requirements.txt`
4. 验证安装

**输出**:
- 虚拟环境创建成功
- 所有依赖安装成功

**验证方法**:
```bash
pip list
python -c "import fastapi; print(fastapi.__version__)"
```

**回滚方案**:
```bash
# 删除虚拟环境
rm -rf venv
```

**验收标准**:
- [ ] FastAPI 安装成功
- [ ] 所有依赖安装成功
- [ ] 无安装错误

---

### 任务 12: 创建 FastAPI 基础应用
**任务 ID**: ENV-001-T12
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Python 依赖已安装

**执行步骤**:
1. 编辑 code/backend/main.py
2. 创建 FastAPI 应用实例
3. 添加健康检查端点
4. 添加 CORS 中间件
5. 启动测试服务器

**输出**:
- code/backend/main.py 文件
- 健康检查端点

**验证方法**:
```bash
cd code/backend
uvicorn main:app --reload
curl http://localhost:8000/health
```

**回滚方案**:
```bash
# 回滚 main.py
git checkout HEAD~1 code/backend/main.py
```

**验收标准**:
- [ ] FastAPI 应用启动成功
- [ ] 健康检查端点返回正常
- [ ] CORS 配置正确

---

### 任务 13: 创建前端项目结构
**任务 ID**: ENV-001-T13
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 项目目录已创建

**执行步骤**:
1. 创建 code/frontend 目录
2. 创建 package.json 文件
3. 创建 index.html 文件
4. 创建 src/ 目录
5. 创建 vite.config.js 文件

**输出**:
- code/frontend/ 目录结构
- package.json 文件

**验证方法**:
```bash
tree code/frontend
cat code/frontend/package.json
```

**回滚方案**:
```bash
rm -rf code/frontend
```

**验收标准**:
- [ ] 目录结构完整
- [ ] package.json 配置正确
- [ ] Vite 配置正确

---

### 任务 14: 安装 Node.js 依赖
**任务 ID**: ENV-001-T14
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- package.json 已创建
- Node.js 20+ 已安装

**执行步骤**:
1. 进入 code/frontend 目录
2. 执行 `npm install`
3. 安装 Vue 3
4. 安装 Element Plus
5. 验证安装

**输出**:
- node_modules/ 目录
- 所有依赖安装成功

**验证方法**:
```bash
cd code/frontend
npm list vue @element-plus
```

**回滚方案**:
```bash
# 删除 node_modules
rm -rf node_modules
```

**验收标准**:
- [ ] Vue 3 安装成功
- [ ] Element Plus 安装成功
- [ ] 无安装错误

---

### 任务 15: 创建 Vue 基础应用
**任务 ID**: ENV-001-T15
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Node.js 依赖已安装

**执行步骤**:
1. 编辑 src/main.js
2. 创建 Vue 应用实例
3. 配置 Element Plus
4. 创建 App.vue 组件
5. 启动开发服务器

**输出**:
- src/main.js 文件
- src/App.vue 文件
- 开发服务器运行中

**验证方法**:
```bash
cd code/frontend
npm run dev
open http://localhost:5173
```

**回滚方案**:
```bash
# 回滚 main.js
git checkout HEAD~1 code/frontend/src/main.js
```

**验收标准**:
- [ ] Vue 应用启动成功
- [ ] Element Plus 配置正确
- [ ] 页面正常显示

---

## 阶段一 -2：Dashboard 集成（第 2 周，04-25 至 05-01）

### 任务 16: 分析 OpenMOSS Dashboard 架构
**任务 ID**: DASH-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- OpenMOSS Dashboard 可访问

**执行步骤**:
1. 访问 http://localhost:6565/dashboard
2. 查看页面结构
3. 分析使用的技术栈
4. 记录 API 端点
5. 记录认证方式

**输出**:
- Dashboard 架构分析文档

**验证方法**:
```bash
cat docs/dashboard-analysis.md
```

**回滚方案**:
```bash
rm docs/dashboard-analysis.md
```

**验收标准**:
- [ ] 技术栈识别正确
- [ ] API 端点记录完整
- [ ] 认证方式记录正确

---

### 任务 17: 测试 OpenMOSS API
**任务 ID**: DASH-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Dashboard 架构分析已完成

**执行步骤**:
1. 测试 GET /api/health 端点
2. 测试 GET /api/tasks 端点
3. 测试 GET /api/agents 端点
4. 记录 API 响应格式
5. 记录认证头

**输出**:
- API 测试结果文档

**验证方法**:
```bash
curl -H "X-Agent-Key: your-key" http://localhost:6565/api/health
```

**回滚方案**:
```bash
rm docs/api-test-results.md
```

**验收标准**:
- [ ] 所有 API 测试成功
- [ ] 响应格式记录完整
- [ ] 认证头记录正确

---

### 任务 18: 实现 iframe 集成方案
**任务 ID**: DASH-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- OpenMOSS API 测试完成
- Vue 应用已创建

**执行步骤**:
1. 创建 src/views/Dashboard.vue 组件
2. 添加 iframe 元素
3. 设置 src 为 OpenMOSS Dashboard URL
4. 配置 iframe 样式（100% 宽高）
5. 添加路由配置

**输出**:
- src/views/Dashboard.vue 文件
- Dashboard 路由配置

**验证方法**:
```bash
cat src/views/Dashboard.vue
```

**回滚方案**:
```bash
# 回滚 Dashboard.vue
git checkout HEAD~1 src/views/Dashboard.vue
```

**验收标准**:
- [ ] iframe 配置正确
- [ ] 样式设置正确
- [ ] 路由配置正确

---

### 任务 19: 配置跨域访问
**任务 ID**: DASH-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- iframe 集成已创建

**执行步骤**:
1. 编辑 OpenMOSS 配置（如果可以）
2. 或者在 Nginx 配置中添加 CORS 头
3. 或者使用浏览器插件临时测试
4. 验证跨域访问

**输出**:
- CORS 配置完成

**验证方法**:
```bash
# 检查浏览器控制台是否有跨域错误
```

**回滚方案**:
```bash
# 回滚 CORS 配置
```

**验收标准**:
- [ ] 无跨域错误
- [ ] iframe 内容正常显示

---

### 任务 20: 实现统一导航栏
**任务 ID**: DASH-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Dashboard iframe 已集成

**执行步骤**:
1. 创建 src/components/Navbar.vue 组件
2. 添加导航链接（首页、项目、模板、Dashboard）
3. 配置路由
4. 添加到 App.vue

**输出**:
- src/components/Navbar.vue 文件
- 统一导航栏

**验证方法**:
```bash
cat src/components/Navbar.vue
```

**回滚方案**:
```bash
rm src/components/Navbar.vue
```

**验收标准**:
- [ ] 导航栏显示正常
- [ ] 所有链接可点击
- [ ] 路由跳转正常

---

### 任务 21: 实现统一认证（JWT 集成）
**任务 ID**: DASH-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 统一导航栏已创建
- JWT 认证系统已完成（阶段 0）

**执行步骤**:
1. 创建 src/utils/auth.js 文件
2. 实现 getToken 函数
3. 实现 setToken 函数
4. 在 API 请求中附加 Token
5. 测试认证流程

**输出**:
- src/utils/auth.js 文件
- 统一认证机制

**验证方法**:
```python
# 测试登录→访问 Dashboard 流程
```

**回滚方案**:
```bash
rm src/utils/auth.js
```

**验收标准**:
- [ ] Token 存储正确
- [ ] API 请求附加 Token
- [ ] 认证流程正常

---

### 任务 22: 测试 Dashboard 集成
**任务 ID**: DASH-001-T07
**预计时长**: 15 分钟
**负责人**: 全员

**输入**:
- Dashboard iframe 已集成
- 统一导航栏已创建
- 统一认证已实现

**执行步骤**:
1. 启动前端应用
2. 访问 Dashboard 页面
3. 测试导航栏
4. 测试认证流程
5. 记录问题

**输出**:
- Dashboard 集成测试报告

**验证方法**:
```bash
open http://localhost:5173/dashboard
```

**回滚方案**:
```bash
# 记录问题并修复
```

**验收标准**:
- [ ] Dashboard 正常显示
- [ ] 导航栏工作正常
- [ ] 认证流程正常
- [ ] 无控制台错误

---

### 任务 23: 创建 OpenMOSS API 客户端
**任务 ID**: API-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- Dashboard 集成测试完成
- FastAPI 应用已创建

**执行步骤**:
1. 创建 code/backend/services/openmoss_client.py
2. 实现 OpenMOSSClient 类
3. 实现 __init__ 方法（配置 base_url 和 api_key）
4. 实现 request 方法（封装 HTTP 请求）

**输出**:
- code/backend/services/openmoss_client.py 文件
- OpenMOSSClient 类

**验证方法**:
```python
from services.openmoss_client import OpenMOSSClient
client = OpenMOSSClient("http://localhost:6565", "api_key")
```

**回滚方案**:
```bash
rm code/backend/services/openmoss_client.py
```

**验收标准**:
- [ ] 类创建成功
- [ ] 配置正确
- [ ] 可以实例化

---

### 任务 24: 实现创建任务 API
**任务 ID**: API-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- OpenMOSSClient 已创建

**执行步骤**:
1. 实现 create_task 方法
2. 实现 POST /api/tasks 端点
3. 调用 OpenMOSS API
4. 返回任务 ID

**输出**:
- create_task 方法
- POST /api/tasks 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name":"测试任务"}'
```

**回滚方案**:
```bash
# 回滚 create_task 方法
git checkout HEAD~1 code/backend/services/openmoss_client.py
```

**验收标准**:
- [ ] 任务创建成功
- [ ] 返回任务 ID
- [ ] OpenMOSS 中有记录

---

### 任务 25: 实现查询任务 API
**任务 ID**: API-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- create_task 方法已实现

**执行步骤**:
1. 实现 get_tasks 方法
2. 实现 GET /api/tasks 端点
3. 支持分页和过滤
4. 返回任务列表

**输出**:
- get_tasks 方法
- GET /api/tasks 端点

**验证方法**:
```bash
curl http://localhost:8000/api/tasks?page=1&size=10
```

**回滚方案**:
```bash
# 回滚 get_tasks 方法
```

**验收标准**:
- [ ] 任务列表查询成功
- [ ] 分页正确
- [ ] 过滤正确

---

### 任务 26: 实现查询任务状态 API
**任务 ID**: API-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- get_tasks 方法已实现

**执行步骤**:
1. 实现 get_task_status 方法
2. 实现 GET /api/tasks/{task_id}/status 端点
3. 返回任务状态

**输出**:
- get_task_status 方法
- GET /api/tasks/{task_id}/status 端点

**验证方法**:
```bash
curl http://localhost:8000/api/tasks/uuid/status
```

**回滚方案**:
```bash
# 回滚 get_task_status 方法
```

**验收标准**:
- [ ] 任务状态查询成功
- [ ] 状态格式正确

---

### 任务 27: 实现 Agent 管理 API
**任务 ID**: API-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- get_task_status 方法已实现

**执行步骤**:
1. 实现 get_agents 方法
2. 实现 GET /api/agents 端点
3. 返回 Agent 列表

**输出**:
- get_agents 方法
- GET /api/agents 端点

**验证方法**:
```bash
curl http://localhost:8000/api/agents
```

**回滚方案**:
```bash
# 回滚 get_agents 方法
```

**验收标准**:
- [ ] Agent 列表查询成功
- [ ] 格式正确

---

### 任务 28: 编写 API 单元测试
**任务 ID**: API-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有 API 端点已创建

**执行步骤**:
1. 创建 tests/test_openmoss_api.py
2. 编写创建任务测试
3. 编写查询任务测试
4. 编写 Agent 管理测试
5. 运行测试

**输出**:
- tests/test_openmoss_api.py 文件
- 测试报告

**验证方法**:
```bash
pytest tests/test_openmoss_api.py -v
```

**回滚方案**:
```bash
rm tests/test_openmoss_api.py
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率≥80%

---

### 任务 29: 实现 YAML 模板解析器
**任务 ID**: TMPL-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- Python 环境
- PyYAML 库

**执行步骤**:
1. 安装 PyYAML：`pip install pyyaml`
2. 创建 code/backend/services/template_parser.py
3. 实现 parse_yaml 函数
4. 实现 validate_template 函数（基础验证）

**输出**:
- code/backend/services/template_parser.py 文件
- parse_yaml 函数
- validate_template 函数

**验证方法**:
```python
from services.template_parser import parse_yaml
yaml_content = "name: test\nversion: '1.0'"
template = parse_yaml(yaml_content)
assert template["name"] == "test"
```

**回滚方案**:
```bash
rm code/backend/services/template_parser.py
```

**验收标准**:
- [ ] YAML 解析正确
- [ ] 基础验证正确

---

### 任务 30: 实现关键词模板匹配
**任务 ID**: TMPL-001-T02
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- template_parser.py 已创建

**执行步骤**:
1. 创建 code/backend/services/template_matcher.py
2. 实现 extract_keywords 函数
3. 实现 keyword_match 函数
4. 实现 calculate_score 函数

**输出**:
- code/backend/services/template_matcher.py 文件
- 3 个匹配函数

**验证方法**:
```python
from services.template_matcher import keyword_match
score = keyword_match(["用户管理"], ["用户", "管理"])
assert score > 0.5
```

**回滚方案**:
```bash
rm code/backend/services/template_matcher.py
```

**验收标准**:
- [ ] 关键词提取正确
- [ ] 匹配分数计算正确

---

### 任务 31: 创建 simple-webpage 模板
**任务 ID**: TMPL-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- template_parser.py 已创建
- template_matcher.py 已创建

**执行步骤**:
1. 创建 templates/simple-webpage.yaml
2. 定义 3 个 Phase（需求、设计、开发）
3. 定义每个 Phase 的 Task
4. 通过 API 导入模板

**输出**:
- templates/simple-webpage.yaml 文件

**验证方法**:
```bash
cat templates/simple-webpage.yaml
```

**回滚方案**:
```bash
rm templates/simple-webpage.yaml
```

**验收标准**:
- [ ] YAML 格式正确
- [ ] Phase 定义完整
- [ ] Task 定义完整

---

### 任务 32: 创建 todo-app 模板
**任务 ID**: TMPL-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- simple-webpage 模板已创建

**执行步骤**:
1. 创建 templates/todo-app.yaml
2. 定义 4 个 Phase（需求、设计、开发、测试）
3. 定义并行执行
4. 通过 API 导入模板

**输出**:
- templates/todo-app.yaml 文件

**验证方法**:
```bash
cat templates/todo-app.yaml
```

**回滚方案**:
```bash
rm templates/todo-app.yaml
```

**验收标准**:
- [ ] YAML 格式正确
- [ ] 并行执行定义正确

---

### 任务 33: 实现模板导入 API
**任务 ID**: TMPL-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- todo-app 模板已创建

**执行步骤**:
1. 实现 POST /api/templates/import 端点
2. 解析 YAML 文件
3. 验证模板
4. 存储到数据库

**输出**:
- POST /api/templates/import 端点

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/templates/import \
  --data-binary @templates/todo-app.yaml
```

**回滚方案**:
```bash
# 注释掉端点
```

**验收标准**:
- [ ] 模板导入成功
- [ ] 验证正确
- [ ] 存储成功

---

### 任务 34: 创建 TODO 应用项目
**任务 ID**: DEMO-001-T01
**预计时长**: 15 分钟
**负责人**: 全员

**输入**:
- todo-app 模板已导入
- API 客户端已完成

**执行步骤**:
1. 调用 API 创建项目
2. 使用 todo-app 模板
3. 实例化模板
4. 创建任务

**输出**:
- TODO 应用项目创建成功

**验证方法**:
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"template_id":"todo-app","name":"TODO 应用"}'
```

**回滚方案**:
```bash
# 删除测试项目
curl -X DELETE http://localhost:8000/api/projects/uuid
```

**验收标准**:
- [ ] 项目创建成功
- [ ] 模板实例化成功
- [ ] 任务创建成功

---

### 任务 35: 执行 TODO 应用演示
**任务 ID**: DEMO-001-T02
**预计时长**: 15 分钟
**负责人**: 全员

**输入**:
- TODO 应用项目已创建

**执行步骤**:
1. 执行需求 Phase
2. 执行设计 Phase
3. 执行开发 Phase
4. 执行测试 Phase
5. 记录执行结果

**输出**:
- 项目执行记录
- 各 Phase 产出物

**验证方法**:
```bash
curl http://localhost:8000/api/projects/uuid/status
```

**回滚方案**:
```bash
# 删除测试项目
```

**验收标准**:
- [ ] 所有 Phase 执行成功
- [ ] 产出物完整

---

### 任务 36: 阶段一复审
**任务 ID**: DEMO-001-T03
**预计时长**: 15 分钟
**负责人**: 评审组

**输入**:
- TODO 应用演示已完成
- 所有阶段一任务已完成

**执行步骤**:
1. 准备复审材料
2. 演示 TODO 应用
3. 演示 Dashboard 集成
4. 评审组提问
5. 评审组签字

**输出**:
- reviews/phase1-review-report.md 文件
- 评审组签字

**验证方法**:
```bash
cat reviews/phase1-review-report.md
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

## 阶段一总结

**总任务数**: 36 个
**总工时**: 9 小时（36 × 15 分钟）
**完成率**: 0/36

**关键路径**:
1. 环境搭建（T01-T15）
2. Dashboard 集成（T16-T22）
3. API 客户端（T23-T28）
4. 模板系统（T29-T33）
5. 演示准备（T34-T36）

**依赖关系**:
```
环境搭建 → Dashboard 集成 → API 客户端 → 模板系统 → 演示准备
```

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：待执行*
