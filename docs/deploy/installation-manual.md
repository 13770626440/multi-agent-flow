# 安装手册

## 文档信息
- **文档编号**：INS-001
- **版本**：v1.0
- **创建日期**：2026 年 4 月 9 日
- **状态**：草案，待评审
- **作者**：AI Assistant
- **适用对象**：AI CI/CD Agent、运维工程师

---

## 1. 概述

本手册提供 Multi-Agent Flow 项目的完整安装和部署指南，适用于 AI CI/CD Agent 自动化部署。

### 1.1 系统要求
- **操作系统**：Windows 10/11, Linux (Ubuntu 22.04+), macOS 12+
- **CPU**：8 核以上（推荐 16 核）
- **内存**：16GB 以上（推荐 32GB）
- **磁盘**：100GB 可用空间
- **网络**：需要访问外部 API（OpenAI/Claude）

### 1.2 依赖组件
| 组件 | 版本 | 用途 | 必需 |
|------|------|------|------|
| Docker | 24+ | 容器运行时 | 是 |
| Docker Compose | 2.20+ | 容器编排 | 是 |
| Python | 3.11+ | 后端运行环境 | 是 |
| Node.js | 20+ | 前端构建环境 | 是 |
| PostgreSQL | 15+ | 主数据库 | 是 |
| Redis | 7+ | 缓存 | 是 |
| Qdrant | 1.7+ | 向量数据库 | 是 |
| OpenMOSS | v1.1.3+ | 任务调度 | 是 |
| OpenClaw | 2026.4.5+ | Agent 执行 | 是 |

---

## 2. 快速开始（一键部署）

### 2.1 Windows 系统

#### 2.1.1  prerequisites 检查
```powershell
# 检查 Docker
docker --version

# 检查 Docker Compose
docker-compose --version

# 检查 Python
python --version

# 检查 Node.js
node --version
```

#### 2.1.2 一键部署脚本
```powershell
# 1. 克隆项目（如果还没有）
cd D:\coding
git clone <repository-url> multi-agent-flow
cd multi-agent-flow

# 2. 运行一键部署脚本
.\scripts\deploy-windows.ps1

# 3. 验证部署
curl http://localhost:8000/health
curl http://localhost:6565/dashboard
```

#### 2.1.3 部署脚本内容（deploy-windows.ps1）
```powershell
# deploy-windows.ps1
# Multi-Agent Flow Windows 一键部署脚本

Write-Host "=== Multi-Agent Flow 部署脚本 ===" -ForegroundColor Green

# 1. 检查 Docker
Write-Host "检查 Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "错误：Docker 未安装，请先安装 Docker Desktop" -ForegroundColor Red
    exit 1
}

# 2. 创建.env 文件
Write-Host "创建环境配置..." -ForegroundColor Yellow
@'
# 数据库配置
POSTGRES_USER=multiagent
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=multiagent

# Redis 配置
REDIS_PASSWORD=your_redis_password

# OpenMOSS 配置
OPENMOSS_API_KEY=your_openmoss_api_key

# OpenAI API（可选）
OPENAI_API_KEY=your_openai_api_key
'@ | Out-File -FilePath .env -Encoding UTF8

# 3. 启动 Docker Compose
Write-Host "启动 Docker 容器..." -ForegroundColor Yellow
docker-compose up -d

# 4. 等待服务就绪
Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 5. 验证服务
Write-Host "验证服务..." -ForegroundColor Yellow
$services = @(
    "http://localhost:8000/health",
    "http://localhost:6565/api/health"
)

foreach ($url in $services) {
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ $url 正常" -ForegroundColor Green
        }
    } catch {
        Write-Host "✗ $url 失败" -ForegroundColor Red
    }
}

Write-Host "=== 部署完成 ===" -ForegroundColor Green
Write-Host "访问 Dashboard: http://localhost:8000" -ForegroundColor Cyan
Write-Host "访问 OpenMOSS Dashboard: http://localhost:6565/dashboard" -ForegroundColor Cyan
```

### 2.2 Linux 系统

#### 2.2.1 prerequisites 检查
```bash
# 检查 Docker
docker --version

# 检查 Docker Compose
docker-compose --version

# 检查 Python
python3 --version

# 检查 Node.js
node --version
```

#### 2.2.2 一键部署脚本
```bash
#!/bin/bash
# deploy-linux.sh
# Multi-Agent Flow Linux 一键部署脚本

echo "=== Multi-Agent Flow 部署脚本 ==="

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误：Docker 未安装"
    exit 1
fi

# 2. 创建.env 文件
echo "创建环境配置..."
cat > .env << EOF
# 数据库配置
POSTGRES_USER=multiagent
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=multiagent

# Redis 配置
REDIS_PASSWORD=your_redis_password

# OpenMOSS 配置
OPENMOSS_API_KEY=your_openmoss_api_key

# OpenAI API（可选）
OPENAI_API_KEY=your_openai_api_key
EOF

# 3. 启动 Docker Compose
echo "启动 Docker 容器..."
docker-compose up -d

# 4. 等待服务就绪
echo "等待服务启动..."
sleep 30

# 5. 验证服务
echo "验证服务..."
curl -f http://localhost:8000/health && echo "✓ Backend 正常" || echo "✗ Backend 失败"
curl -f http://localhost:6565/api/health && echo "✓ OpenMOSS 正常" || echo "✗ OpenMOSS 失败"

echo "=== 部署完成 ==="
echo "访问 Dashboard: http://localhost:8000"
echo "访问 OpenMOSS Dashboard: http://localhost:6565/dashboard"
```

执行：
```bash
chmod +x scripts/deploy-linux.sh
./scripts/deploy-linux.sh
```

### 2.3 macOS 系统

#### 2.3.1 prerequisites 检查
```bash
# 检查 Docker
docker --version

# 检查 Docker Compose
docker-compose --version

# 检查 Python
python3 --version

# 检查 Node.js
node --version
```

#### 2.3.2 一键部署脚本
```bash
#!/bin/bash
# deploy-macos.sh
# Multi-Agent Flow macOS 一键部署脚本

echo "=== Multi-Agent Flow 部署脚本 ==="

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误：Docker 未安装，请先安装 Docker Desktop"
    exit 1
fi

# 2. 创建.env 文件
echo "创建环境配置..."
cat > .env << EOF
POSTGRES_USER=multiagent
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=multiagent
REDIS_PASSWORD=your_redis_password
OPENMOSS_API_KEY=your_openmoss_api_key
OPENAI_API_KEY=your_openai_api_key
EOF

# 3. 启动 Docker Compose
echo "启动 Docker 容器..."
docker-compose up -d

# 4. 等待服务就绪
echo "等待服务启动..."
sleep 30

# 5. 验证服务
echo "验证服务..."
curl -f http://localhost:8000/health && echo "✓ Backend 正常" || echo "✗ Backend 失败"
curl -f http://localhost:6565/api/health && echo "✓ OpenMOSS 正常" || echo "✗ OpenMOSS 失败"

echo "=== 部署完成 ==="
echo "访问 Dashboard: http://localhost:8000"
echo "访问 OpenMOSS Dashboard: http://localhost:6565/dashboard"
```

执行：
```bash
chmod +x scripts/deploy-macos.sh
./scripts/deploy-macos.sh
```

---

## 3. 详细部署步骤

### 3.1 环境准备

#### 3.1.1 安装 Docker
**Windows/macOS**：
1. 下载 Docker Desktop：https://www.docker.com/products/docker-desktop
2. 安装并启动 Docker Desktop
3. 验证安装：`docker --version`

**Linux (Ubuntu)**：
```bash
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
```

#### 3.1.2 安装 Docker Compose
**Windows/macOS**：Docker Desktop 已包含

**Linux**：
```bash
# 下载 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 3.2 配置文件

#### 3.2.1 docker-compose.yml
```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    container_name: multi-agent-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-multiagent}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeit}
      POSTGRES_DB: multiagent
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-multiagent}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: multi-agent-redis
    command: redis-server --requirepass ${REDIS_PASSWORD:-changeit}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Qdrant 向量数据库
  qdrant:
    image: qdrant/qdrant:v1.7.0
    container_name: multi-agent-qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"

  # OpenMOSS
  openmoss:
    image: uluckyXH/openmoss:v1.1.3
    container_name: multi-agent-openmoss
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-multiagent}:${POSTGRES_PASSWORD:-changeit}@postgres:5432/multiagent
      API_KEY: ${OPENMOSS_API_KEY:-openmoss_api_key}
    ports:
      - "6565:6565"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6565/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 后端服务
  backend:
    build:
      context: ./code/backend
      dockerfile: Dockerfile
    container_name: multi-agent-backend
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-multiagent}:${POSTGRES_PASSWORD:-changeit}@postgres:5432/multiagent
      REDIS_URL: redis://:${REDIS_PASSWORD:-changeit}@redis:6379/0
      QDRANT_URL: http://qdrant:6333
      OPENMOSS_URL: http://openmoss:6565
      OPENMOSS_API_KEY: ${OPENMOSS_API_KEY:-openmoss_api_key}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      openmoss:
        condition: service_healthy
    volumes:
      - ./code/backend:/app
      - shared_workspace:/app/shared

  # 前端服务
  frontend:
    build:
      context: ./code/frontend
      dockerfile: Dockerfile
    container_name: multi-agent-frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  shared_workspace:
```

#### 3.2.2 .env.example
```bash
# 数据库配置
POSTGRES_USER=multiagent
POSTGRES_PASSWORD=changeit
POSTGRES_DB=multiagent

# Redis 配置
REDIS_PASSWORD=changeit

# Qdrant 配置
QDRANT_API_KEY=

# OpenMOSS 配置
OPENMOSS_API_KEY=openmoss_api_key

# OpenAI API（可选）
OPENAI_API_KEY=

# 日志级别
LOG_LEVEL=INFO
```

### 3.3 数据库初始化

#### 3.3.1 创建数据库表
```bash
# 进入 PostgreSQL 容器
docker exec -it multi-agent-postgres psql -U multiagent -d multiagent

# 执行初始化脚本
psql> \i /docker-entrypoint-initdb.d/init.sql
```

#### 3.3.2 初始化脚本（init.sql）
```sql
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建 templates 表
CREATE TABLE IF NOT EXISTS templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    yaml_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    success_rate DECIMAL(5,2),
    usage_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE (name, version)
);

-- 创建 projects 表
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    template_id VARCHAR(50) REFERENCES templates(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    expected_duration INTERVAL,
    actual_duration INTERVAL,
    success_score DECIMAL(5,2),
    metadata JSONB
);

-- 创建 agencies 表
CREATE TABLE IF NOT EXISTS agencies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    responsibilities JSONB,
    required_skills JSONB,
    career_path JSONB,
    performance_metrics JSONB,
    promotion_criteria JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建 agents 表
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(50) PRIMARY KEY,
    agency_id VARCHAR(50) REFERENCES agencies(id),
    name VARCHAR(100) NOT NULL,
    level VARCHAR(20) DEFAULT 'Junior',
    experience_points INTEGER DEFAULT 0,
    skill_mastery JSONB,
    project_history JSONB,
    performance_metrics JSONB,
    status VARCHAR(20) DEFAULT 'idle',
    current_project_id VARCHAR(50) REFERENCES projects(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建 skills 表
CREATE TABLE IF NOT EXISTS skills (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    content JSONB NOT NULL,
    source_project_id VARCHAR(50) REFERENCES projects(id),
    usage_count INTEGER DEFAULT 0,
    effectiveness_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建 project_metrics 表
CREATE TABLE IF NOT EXISTS project_metrics (
    id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50) REFERENCES projects(id),
    phase_name VARCHAR(100),
    duration INTERVAL,
    review_score DECIMAL(5,2),
    rework_count INTEGER,
    bug_count INTEGER,
    test_coverage DECIMAL(5,2),
    agent_performance JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_templates_name ON templates(name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_agents_agency ON agents(agency_id);
CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);
```

### 3.4 服务启动

#### 3.4.1 启动所有服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 3.4.2 停止所有服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（危险操作！）
docker-compose down -v
```

#### 3.4.3 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 3.5 验证部署

#### 3.5.1 健康检查
```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查 OpenMOSS
curl http://localhost:6565/api/health

# 检查 PostgreSQL
docker exec multi-agent-postgres pg_isready -U multiagent

# 检查 Redis
docker exec multi-agent-redis redis-cli ping

# 检查 Qdrant
curl http://localhost:6333/
```

#### 3.5.2 访问 Dashboard
```bash
# 主 Dashboard
open http://localhost:8000

# OpenMOSS Dashboard
open http://localhost:6565/dashboard
```

#### 3.5.3 测试 API
```bash
# 获取模板列表
curl http://localhost:8000/api/templates

# 创建测试项目
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试项目",
    "template_id": "test-template"
  }'
```

---

## 4. 故障排查

### 4.1 常见问题

#### 4.1.1 Docker 容器无法启动
**症状**：`docker-compose up` 报错
**解决方案**：
```bash
# 1. 检查 Docker 是否运行
docker ps

# 2. 查看容器日志
docker-compose logs <service-name>

# 3. 清理并重新启动
docker-compose down
docker-compose up -d
```

#### 4.1.2 数据库连接失败
**症状**：后端服务报错"无法连接数据库"
**解决方案**：
```bash
# 1. 检查 PostgreSQL 是否运行
docker exec multi-agent-postgres pg_isready -U multiagent

# 2. 检查数据库密码
docker-compose logs postgres | grep "password"

# 3. 重启数据库
docker-compose restart postgres
```

#### 4.1.3 OpenMOSS 集成失败
**症状**：调用 OpenMOSS API 失败
**解决方案**：
```bash
# 1. 检查 OpenMOSS 是否运行
curl http://localhost:6565/api/health

# 2. 检查 API Key
docker-compose logs backend | grep "OPENMOSS"

# 3. 检查网络连接
docker exec multi-agent-backend ping openmoss
```

### 4.2 日志查看

#### 4.2.1 查看所有服务日志
```bash
docker-compose logs -f
```

#### 4.2.2 查看特定服务日志
```bash
# 查看后端日志
docker-compose logs -f backend

# 查看数据库日志
docker-compose logs -f postgres

# 查看 OpenMOSS 日志
docker-compose logs -f openmoss
```

#### 4.2.3 导出日志
```bash
# 导出后端日志到文件
docker-compose logs backend > logs/backend-$(date +%Y%m%d).log
```

### 4.3 性能优化

#### 4.3.1 数据库优化
```sql
-- 分析慢查询
EXPLAIN ANALYZE SELECT * FROM projects WHERE status = 'in_progress';

-- 添加索引
CREATE INDEX idx_projects_status_created ON projects(status, created_at);

-- 清理旧数据
DELETE FROM project_metrics WHERE created_at < NOW() - INTERVAL '30 days';
```

#### 4.3.2 缓存优化
```bash
# 检查 Redis 内存使用
docker exec multi-agent-redis redis-cli INFO memory

# 清理 Redis 缓存
docker exec multi-agent-redis redis-cli FLUSHDB
```

---

## 5. 备份与恢复

### 5.1 数据库备份
```bash
# 备份 PostgreSQL 数据库
docker exec multi-agent-postgres pg_dump -U multiagent multiagent > backup-$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i multi-agent-postgres psql -U multiagent -d multiagent < backup-20260409.sql
```

### 5.2 数据卷备份
```bash
# 备份数据卷
docker run --rm \
  -v multi-agent-flow_postgres_data:/data/source \
  -v $(pwd):/data/backup \
  alpine tar czf /data/backup/postgres-backup.tar.gz -C /data/source .

# 恢复数据卷
docker run --rm \
  -v multi-agent-flow_postgres_data:/data/target \
  -v $(pwd):/data/backup \
  alpine tar xzf /data/backup/postgres-backup.tar.gz -C /data/target
```

---

## 6. 升级指南

### 6.1 升级 Docker 镜像
```bash
# 拉取最新镜像
docker-compose pull

# 停止服务
docker-compose down

# 启动新服务
docker-compose up -d

# 验证升级
docker-compose ps
```

### 6.2 数据库迁移
```bash
# 运行数据库迁移脚本
docker exec multi-agent-postgres psql -U multiagent -d multiagent -f /migrations/upgrade.sql
```

---

## 7. 安全配置

### 7.1 修改默认密码
```bash
# 编辑.env 文件
vi .env

# 修改以下配置
POSTGRES_PASSWORD=strong_password_here
REDIS_PASSWORD=strong_password_here
OPENMOSS_API_KEY=secure_api_key_here
```

### 7.2 防火墙配置
```bash
# Linux 防火墙配置
sudo ufw allow 8000/tcp  # 后端
sudo ufw allow 6565/tcp  # OpenMOSS
sudo ufw allow 80/tcp    # 前端

# 限制数据库访问
sudo ufw deny 5432/tcp   # PostgreSQL（仅内网）
sudo ufw deny 6379/tcp   # Redis（仅内网）
```

---

## 8. 监控与告警

### 8.1 健康检查端点
```bash
# 后端健康检查
curl http://localhost:8000/health

# OpenMOSS 健康检查
curl http://localhost:6565/api/health
```

### 8.2 监控指标
- CPU 使用率
- 内存使用率
- 磁盘使用率
- API 响应时间
- 数据库连接数

### 8.3 告警配置
```yaml
# prometheus-alerts.yml
groups:
  - name: multi-agent-alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage > 80
        for: 5m
        annotations:
          summary: "CPU 使用率过高"
      
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        annotations:
          summary: "服务宕机"
```

---

## 9. 附录

### 9.1 端口清单
| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| 后端 API | 8000 | HTTP | FastAPI 服务 |
| 前端 | 80 | HTTP | Nginx + Vue |
| OpenMOSS | 6565 | HTTP | OpenMOSS API |
| PostgreSQL | 5432 | TCP | 数据库 |
| Redis | 6379 | TCP | 缓存 |
| Qdrant | 6333 | HTTP | 向量数据库 |

### 9.2 环境变量清单
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| POSTGRES_USER | multiagent | 数据库用户 |
| POSTGRES_PASSWORD | changeit | 数据库密码 |
| REDIS_PASSWORD | changeit | Redis 密码 |
| OPENMOSS_API_KEY | openmoss_api_key | OpenMOSS API 密钥 |
| OPENAI_API_KEY | - | OpenAI API 密钥 |
| LOG_LEVEL | INFO | 日志级别 |

### 9.3 参考文档
- Docker 文档：https://docs.docker.com
- Docker Compose 文档：https://docs.docker.com/compose
- OpenMOSS 文档：https://github.com/uluckyXH/OpenMOSS
- OpenClaw 文档：https://openclawapi.org

---

*文档结束*
*最后更新：2026-04-09*
