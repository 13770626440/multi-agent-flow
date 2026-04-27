# TC-E2E-00 冒烟测试自动化执行脚本
# 用途：验证 Agent 系统基础运行环境
# 执行方式：在 multi-agent-flow 项目根目录运行此脚本

$ErrorActionPreference = "Stop"
$ProjectRoot = "D:\coding\multi-agent-flow"
$TemplateEditor = "$ProjectRoot\docs\template\template_editor"
$TemplateDir = "$ProjectRoot\docs\template"
$TemplateFile = "e2e-smoke-test.yaml"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TC-E2E-00: 基础设施验证与冒烟测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 验证模板文件存在
Write-Host "[步骤 1] 验证模板文件..." -ForegroundColor Yellow
$TemplatePath = Join-Path $TemplateEditor $TemplateFile
if (Test-Path $TemplatePath) {
    Write-Host "  ✅ 模板文件存在: $TemplatePath" -ForegroundColor Green
    $Content = Get-Content $TemplatePath -Raw
    
    # 验证必需字段
    $RequiredFields = @("template_id:", "version:", "roles:", "tasks:")
    $AllFieldsPresent = $true
    foreach ($field in $RequiredFields) {
        if ($Content -notmatch [regex]::Escape($field)) {
            Write-Host "  ❌ 缺少必需字段: $field" -ForegroundColor Red
            $AllFieldsPresent = $false
        }
    }
    if ($AllFieldsPresent) {
        Write-Host "  ✅ 所有必需字段存在" -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ 模板文件不存在: $TemplatePath" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 2: 环境可用性验证
Write-Host "[步骤 2] 环境可用性验证..." -ForegroundColor Yellow

# PostgreSQL
Write-Host "  检查 PostgreSQL..." -NoNewline
try {
    $Result = docker exec maf-postgres pg_isready 2>&1
    if ($Result -match "accepting connections") {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "    输出: $Result" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ (容器可能未运行)" -ForegroundColor Red
}

# Redis
Write-Host "  检查 Redis..." -NoNewline
try {
    $Result = docker exec maf-redis redis-cli ping 2>&1
    if ($Result -match "PONG") {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "    输出: $Result" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ (容器可能未运行)" -ForegroundColor Red
}

# Backend
Write-Host "  检查 Backend..." -NoNewline
try {
    $Response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($Response.StatusCode -eq 200) {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌ (HTTP $($Response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ (无法连接)" -ForegroundColor Red
}

# OpenClaw
Write-Host "  检查 OpenClaw..." -NoNewline
try {
    $Result = docker exec maf-openclaw openclaw status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ (容器可能未运行)" -ForegroundColor Red
}

# OpenMOSS
Write-Host "  检查 OpenMOSS..." -NoNewline
try {
    $Response = Invoke-WebRequest -Uri "http://127.0.0.1:6565/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($Response.StatusCode -eq 200) {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌ (HTTP $($Response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ (无法连接)" -ForegroundColor Red
}

Write-Host ""

# 步骤 3: 复制模板触发加载
Write-Host "[步骤 3] 复制模板到 template 目录..." -ForegroundColor Yellow
$DestPath = Join-Path $TemplateDir $TemplateFile
try {
    Copy-Item -Path $TemplatePath -Destination $DestPath -Force
    Write-Host "  ✅ 模板已复制: $DestPath" -ForegroundColor Green
    Write-Host "  ⏳ 等待 Backend 加载模板 (3 秒)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
} catch {
    Write-Host "  ❌ 复制失败: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 4: 验证 Backend 日志
Write-Host "[步骤 4] 检查 Backend 日志..." -ForegroundColor Yellow
try {
    $Logs = docker logs maf-backend --since 10s 2>&1
    if ($Logs -match "Template e2e-smoke-test.*loaded successfully") {
        Write-Host "  ✅ 模板加载成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 未找到模板加载成功日志" -ForegroundColor Red
        Write-Host "  最近日志:" -ForegroundColor Yellow
        $Logs | Select-Object -Last 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
    
    if ($Logs -match "AgentProvisioner.*smoke-test-agent") {
        Write-Host "  ✅ Agent 动态供给已触发" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  未找到 Agent 供给日志 (可能已存在)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 无法获取 Backend 日志: $_" -ForegroundColor Red
}
Write-Host ""

# 步骤 5: 验证 Redis 缓存
Write-Host "[步骤 5] 验证 Redis 缓存..." -ForegroundColor Yellow
try {
    $Result = docker exec maf-redis redis-cli GET "template:e2e-smoke-test" 2>&1
    if ($Result -and $Result -notmatch "^$") {
        Write-Host "  ✅ Redis 缓存存在" -ForegroundColor Green
        # 解析 JSON 验证
        try {
            $Json = $Result | ConvertFrom-Json
            Write-Host "  ✅ 模板 ID: $($Json.template_id)" -ForegroundColor Green
            Write-Host "  ✅ 版本: $($Json.version)" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️  JSON 解析失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ Redis 缓存不存在" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ 无法连接 Redis: $_" -ForegroundColor Red
}
Write-Host ""

# 步骤 6: 验证 Agent 状态
Write-Host "[步骤 6] 验证 Agent 状态..." -ForegroundColor Yellow
try {
    $Result = docker exec maf-openclaw openclaw agents list 2>&1
    if ($Result -match "smoke-test-agent") {
        Write-Host "  ✅ Agent 'smoke-test-agent' 已创建" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Agent 未在列表中 (可能未同步)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 无法获取 Agent 列表: $_" -ForegroundColor Red
}
Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请检查以上输出，确认所有步骤是否通过。" -ForegroundColor White
Write-Host "如需查看详细日志，运行: docker logs maf-backend --since 5m" -ForegroundColor Gray
Write-Host ""
