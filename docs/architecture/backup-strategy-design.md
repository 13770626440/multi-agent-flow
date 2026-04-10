# 备份策略设计

## 文档信息
- **文档编号**: BAK-001
- **版本**: v1.0
- **创建日期**: 2026 年 4 月 9 日
- **状态**: 已实施
- **作者**: AI Assistant（架构师）

---

## 1. 备份架构

### 1.1 备份层次
```
备份系统
├── 数据库备份
│   ├── 全量备份（每日）
│   ├── 增量备份（每小时）
│   └── WAL 归档（实时）
├── 文件备份
│   ├── 配置文件
│   ├── 用户上传文件
│   └── 日志文件
└── 代码备份
    └── Git 仓库远程备份
```

### 1.2 备份目标
- **RPO（Recovery Point Objective）**: 1 小时（最多丢失 1 小时数据）
- **RTO（Recovery Time Objective）**: 4 小时（4 小时内恢复）

---

## 2. 数据库备份

### 2.1 全量备份脚本
```bash
#!/bin/bash
# daily_backup.sh
# 每日全量备份脚本

set -e

# 配置
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7
DB_NAME="multiagent"
DB_USER="multiagent"
DB_HOST="localhost"

# 创建备份目录
mkdir -p ${BACKUP_DIR}/daily

# 全量备份
echo "[$(date)] 开始全量备份..."
pg_dump -U ${DB_USER} -h ${DB_HOST} -Fc ${DB_NAME} > ${BACKUP_DIR}/daily/full_${DATE}.dump

# 压缩
echo "[$(date)] 压缩备份文件..."
gzip ${BACKUP_DIR}/daily/full_${DATE}.dump

# 验证备份
echo "[$(date)] 验证备份..."
if pg_restore --list ${BACKUP_DIR}/daily/full_${DATE}.dump.gz > /dev/null; then
    echo "[$(date)] 备份验证成功"
else
    echo "[$(date)] 备份验证失败"
    exit 1
fi

# 清理旧备份
echo "[$(date)] 清理 ${RETENTION_DAYS} 天前的备份..."
find ${BACKUP_DIR}/daily -name "full_*.dump.gz" -mtime +${RETENTION_DAYS} -delete

# 上传到对象存储（可选）
if [ -n "${AWS_S3_BUCKET}" ]; then
    echo "[$(date)] 上传到 S3..."
    aws s3 cp ${BACKUP_DIR}/daily/full_${DATE}.dump.gz s3://${AWS_S3_BUCKET}/postgresql/daily/
fi

echo "[$(date)] 备份完成：${BACKUP_DIR}/daily/full_${DATE}.dump.gz"
```

### 2.2 增量备份脚本
```bash
#!/bin/bash
# hourly_backup.sh
# 每小时增量备份脚本

set -e

# 配置
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_HOURS=24
DB_NAME="multiagent"
DB_USER="multiagent"

# 创建备份目录
mkdir -p ${BACKUP_DIR}/hourly

# WAL 归档备份
echo "[$(date)] 开始 WAL 归档备份..."
pg_basebackup -U ${DB_USER} -D ${BACKUP_DIR}/hourly/base_${DATE} -Ft -z -Xs -P

# 清理旧备份
echo "[$(date)] 清理 ${RETENTION_HOURS} 小时前的备份..."
find ${BACKUP_DIR}/hourly -name "base_*.tar.gz" -mtime -${RETENTION_HOURS}/24 -delete
```

### 2.3 定时任务配置
```bash
# /etc/crontab

# 每日凌晨 2 点全量备份
0 2 * * * root /scripts/daily_backup.sh >> /var/log/backup.log 2>&1

# 每小时增量备份
0 * * * * root /scripts/hourly_backup.sh >> /var/log/backup.log 2>&1

# 每周日凌晨 3 点备份验证
0 3 * * 0 root /scripts/verify_backup.sh >> /var/log/backup.log 2>&1
```

---

## 3. 文件备份

### 3.1 配置文件备份
```bash
#!/bin/bash
# backup_configs.sh

BACKUP_DIR="/backups/configs"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份配置文件
tar -czf ${BACKUP_DIR}/configs_${DATE}.tar.gz \
    /etc/multi-agent-flow/ \
    ~/.openclaw/config.json \
    ~/.openclaw/AGENTS.md \
    /backups/postgresql/

# 上传到对象存储
aws s3 cp ${BACKUP_DIR}/configs_${DATE}.tar.gz s3://${AWS_S3_BUCKET}/configs/
```

### 3.2 日志文件备份
```bash
#!/bin/bash
# backup_logs.sh

BACKUP_DIR="/backups/logs"
DATE=$(date +%Y%m%d)

# 压缩旧日志
find /var/log/multi-agent-flow/ -name "*.log" -mtime -7 -exec gzip {} \;

# 上传到对象存储
aws s3 sync /var/log/multi-agent-flow/ s3://${AWS_S3_BUCKET}/logs/${DATE}/
```

---

## 4. 备份验证

### 4.1 备份验证脚本
```bash
#!/bin/bash
# verify_backup.sh
# 每周备份验证脚本

set -e

BACKUP_DIR="/backups/postgresql"
TEST_DB="multiagent_test_$(date +%Y%m%d)"

echo "[$(date)] 开始备份验证..."

# 1. 找到最新的备份
LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/daily/full_*.dump.gz | head -1)

if [ -z "${LATEST_BACKUP}" ]; then
    echo "[$(date)] 错误：未找到备份文件"
    exit 1
fi

echo "[$(date)] 验证备份：${LATEST_BACKUP}"

# 2. 解压备份
gunzip -c ${LATEST_BACKUP} > /tmp/latest_backup.dump

# 3. 恢复到测试数据库
echo "[$(date)] 恢复到测试数据库..."
pg_restore -U multiagent -h localhost -d ${TEST_DB} /tmp/latest_backup.dump

# 4. 验证数据完整性
echo "[$(date)] 验证数据完整性..."
TABLE_COUNT=$(psql -U multiagent -h localhost -d ${TEST_DB} -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")

if [ ${TABLE_COUNT} -gt 0 ]; then
    echo "[$(date)] 验证成功：${TABLE_COUNT} 个表"
else
    echo "[$(date)] 验证失败：表数量为 0"
    exit 1
fi

# 5. 清理测试数据库
echo "[$(date)] 清理测试数据库..."
dropdb -U multiagent -h localhost ${TEST_DB}

# 6. 清理临时文件
rm -f /tmp/latest_backup.dump

echo "[$(date)] 备份验证完成"
```

### 4.2 恢复演练
```bash
#!/bin/bash
# recovery_drill.sh
# 每季度恢复演练脚本

set -e

echo "[$(date)] 开始恢复演练..."

# 1. 停止服务
echo "[$(date)] 停止服务..."
systemctl stop multi-agent-flow

# 2. 备份当前数据库（以防万一）
echo "[$(date)] 备份当前数据库..."
pg_dump -U multiagent -h localhost multiagent > /tmp/pre_drill_backup.sql

# 3. 恢复最新备份
echo "[$(date)] 恢复最新备份..."
LATEST_BACKUP=$(ls -t /backups/postgresql/daily/full_*.dump.gz | head -1)
gunzip -c ${LATEST_BACKUP} | pg_restore -U multiagent -h localhost -d multiagent

# 4. 启动服务
echo "[$(date)] 启动服务..."
systemctl start multi-agent-flow

# 5. 验证服务正常
echo "[$(date)] 验证服务..."
sleep 10
curl -f http://localhost:8000/health || exit 1

# 6. 恢复原数据库
echo "[$(date)] 恢复原数据库..."
psql -U multiagent -h localhost -d multiagent < /tmp/pre_drill_backup.sql

# 7. 清理
rm -f /tmp/pre_drill_backup.sql

echo "[$(date)] 恢复演练完成"
```

---

## 5. 灾难恢复计划

### 5.1 恢复流程
```
1. 评估灾难影响
   ↓
2. 通知相关人员
   ↓
3. 准备恢复环境
   ↓
4. 恢复数据库
   ↓
5. 恢复配置文件
   ↓
6. 恢复服务
   ↓
7. 验证服务正常
   ↓
8. 通知用户
```

### 5.2 恢复脚本
```bash
#!/bin/bash
# disaster_recovery.sh
# 灾难恢复脚本

set -e

BACKUP_SOURCE="${1:-/backups/postgresql}"
DB_HOST="${2:-localhost}"

echo "[$(date)] 开始灾难恢复..."

# 1. 创建新数据库
echo "[$(date)] 创建数据库..."
createdb -U multiagent -h ${DB_HOST} multiagent

# 2. 恢复最新备份
echo "[$(date)] 恢复数据库..."
LATEST_BACKUP=$(ls -t ${BACKUP_SOURCE}/daily/full_*.dump.gz | head -1)
gunzip -c ${LATEST_BACKUP} | pg_restore -U multiagent -h ${DB_HOST} -d multiagent

# 3. 恢复配置文件
echo "[$(date)] 恢复配置文件..."
aws s3 cp s3://${AWS_S3_BUCKET}/configs/ /etc/multi-agent-flow/ --recursive

# 4. 验证恢复
echo "[$(date)] 验证恢复..."
TABLE_COUNT=$(psql -U multiagent -h ${DB_HOST} -d multiagent -t -c "SELECT COUNT(*) FROM information_schema.tables")

if [ ${TABLE_COUNT} -gt 0 ]; then
    echo "[$(date)] 恢复成功：${TABLE_COUNT} 个表"
else
    echo "[$(date)] 恢复失败"
    exit 1
fi

echo "[$(date)] 灾难恢复完成"
```

---

## 6. 监控与告警

### 6.1 备份监控
```python
# backup_monitor.py
# 备份监控脚本

import boto3
from datetime import datetime, timedelta

def check_backup_status():
    """
    检查备份状态
    """
    s3 = boto3.client('s3')
    bucket = 'backup-bucket'
    
    # 检查最新备份
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix='postgresql/daily/',
        MaxKeys=1
    )
    
    if 'Contents' not in response:
        send_alert("未找到备份文件")
        return
    
    latest_backup = response['Contents'][0]
    backup_time = latest_backup['LastModified']
    
    # 检查备份是否超过 24 小时
    if datetime.now(backup_time.tzinfo) - backup_time > timedelta(hours=24):
        send_alert("备份超过 24 小时未更新")
    
    # 检查备份大小
    if latest_backup['Size'] < 1024 * 1024:  # 小于 1MB
        send_alert("备份文件过小，可能异常")

def send_alert(message):
    """
    发送告警
    """
    # 发送邮件告警
    send_email(
        to="admin@example.com",
        subject="备份告警",
        body=message
    )
    
    # 发送 Slack 告警
    send_slack_message(message)
```

### 6.2 监控指标
```yaml
备份指标:
  - 备份成功率
    - 告警阈值：< 99%
  - 备份文件大小
    - 告警阈值：< 1MB 或 > 10GB
  - 备份延迟
    - 告警阈值：> 24 小时
  - 恢复演练成功率
    - 告警阈值：< 100%
```

---

## 7. 实施工作量

| 任务 | 工时 | 说明 |
|------|------|------|
| 备份脚本开发 | 2 小时 | 全量 + 增量 + 验证 |
| 定时任务配置 | 1 小时 | crontab 配置 |
| 恢复脚本开发 | 1 小时 | 灾难恢复脚本 |
| 监控脚本开发 | 1 小时 | 备份监控 + 告警 |
| 恢复演练 | 1 小时 | 测试恢复流程 |
| **总计** | **6 小时** | 约 1 个工作日 |

---

## 8. 验收标准

- [ ] 全量备份每日自动执行
- [ ] 增量备份每小时自动执行
- [ ] 备份验证每周自动执行
- [ ] 恢复演练每季度执行
- [ ] 监控告警正常工作
- [ ] 备份文件可成功恢复
- [ ] RPO < 1 小时
- [ ] RTO < 4 小时

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：已实施*
