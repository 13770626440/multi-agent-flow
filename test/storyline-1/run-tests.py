#!/usr/bin/env python3
"""
故事线 1 端到端测试 - 通过 Agent CLI 模拟人机对话

测试纪律：
- 严禁瞒报：所有测试结果如实记录
- 详细保留：所有过程数据、文件、日志均保存
- 通过 Agent CLI 执行，严禁直接调用 API
"""

import subprocess
import json
import time
import os
from datetime import datetime

# 测试配置
TEST_DIR = r"D:\coding\multi-agent-flow\test\storyline-1"
LOG_FILE = os.path.join(TEST_DIR, "test-log.txt")

def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    try:
        print(log_line)
    except UnicodeEncodeError:
        print(log_line.encode('gbk', errors='ignore').decode('gbk'))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def run_agent_command(message: str, session_id: str) -> dict:
    """通过 Agent CLI 执行命令"""
    cmd = [
        "docker", "exec", "maf-openclaw-gateway",
        "openclaw", "agent",
        "--session-id", session_id,
        "--message", message
    ]
    
    log(f"执行 Agent 命令: {message}")
    log(f"Session ID: {session_id}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8')
    except subprocess.TimeoutExpired:
        log("❌ 命令执行超时（120 秒）")
        return {
            "command": " ".join(cmd),
            "stdout": "",
            "stderr": "Timeout expired",
            "returncode": -1,
            "timestamp": datetime.now().isoformat()
        }
    
    output = {
        "command": " ".join(cmd),
        "stdout": result.stdout if result.stdout else "",
        "stderr": result.stderr if result.stderr else "",
        "returncode": result.returncode,
        "timestamp": datetime.now().isoformat()
    }
    
    log(f"返回码: {result.returncode}")
    stdout_preview = (result.stdout or "")[:500]
    log(f"输出预览: {stdout_preview}")
    
    return output

def test_tc_e2e_001():
    """TC-E2E-001: 模板加载验证"""
    log("="*60)
    log("TC-E2E-001: 模板加载验证")
    log("="*60)
    
    # 通过 Agent 查询模板列表
    result = run_agent_command(
        "请查询 simple-dev-flow 模板的详细信息",
        "test-storyline-1"
    )
    
    # 保存结果
    result_file = os.path.join(TEST_DIR, "TC-E2E-001", "agent-response.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    log(f"结果已保存至: {result_file}")
    
    # 验证结果
    if result["returncode"] == 0:
        log("[PASS] TC-E2E-001: 通过")
        return True
    else:
        log("[FAIL] TC-E2E-001: 失败")
        return False

def test_tc_e2e_002():
    """TC-E2E-002: 模板详情验证 - 节点结构"""
    log("="*60)
    log("TC-E2E-002: 模板详情验证 - 节点结构")
    log("="*60)
    
    # 通过 Agent 查询模板节点
    result = run_agent_command(
        "请列出 simple-dev-flow 模板的所有节点，包括节点名称、类型和依赖关系",
        "test-storyline-1"
    )
    
    # 保存结果
    result_file = os.path.join(TEST_DIR, "TC-E2E-002", "agent-response.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    log(f"结果已保存至: {result_file}")
    
    if result["returncode"] == 0:
        log("[PASS] TC-E2E-002: 通过")
        return True
    else:
        log("[FAIL] TC-E2E-002: 失败")
        return False

def test_tc_e2e_003():
    """TC-E2E-003: 模板实例化 - 创建任务"""
    log("="*60)
    log("TC-E2E-003: 模板实例化 - 创建任务")
    log("="*60)
    
    # 通过 Agent 创建任务
    result = run_agent_command(
        "请使用 simple-dev-flow 模板创建一个任务，项目名称为'用户管理系统'，技术栈为'FastAPI + Vue3'",
        "test-storyline-1"
    )
    
    # 保存结果
    result_file = os.path.join(TEST_DIR, "TC-E2E-003", "agent-response.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    log(f"结果已保存至: {result_file}")
    
    if result["returncode"] == 0:
        log("[PASS] TC-E2E-003: 通过")
        return True
    else:
        log("[FAIL] TC-E2E-003: 失败")
        return False

def test_tc_e2e_004():
    """TC-E2E-004: 任务实例详情验证"""
    log("="*60)
    log("TC-E2E-004: 任务实例详情验证")
    log("="*60)
    
    # 通过 Agent 查询任务详情
    result = run_agent_command(
        "请查询刚才创建的任务详情，包括输入参数和节点信息",
        "test-storyline-1"
    )
    
    # 保存结果
    result_file = os.path.join(TEST_DIR, "TC-E2E-004", "agent-response.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    log(f"结果已保存至: {result_file}")
    
    if result["returncode"] == 0:
        log("[PASS] TC-E2E-004: 通过")
        return True
    else:
        log("[FAIL] TC-E2E-004: 失败")
        return False

def main():
    """主测试流程"""
    log("故事线 1 端到端测试开始")
    log(f"测试时间: {datetime.now().isoformat()}")
    
    results = {
        "TC-E2E-001": test_tc_e2e_001(),
        "TC-E2E-002": test_tc_e2e_002(),
        "TC-E2E-003": test_tc_e2e_003(),
        "TC-E2E-004": test_tc_e2e_004()
    }
    
    # 汇总结果
    log("="*60)
    log("测试结果汇总")
    log("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for tc, result in results.items():
        status = "[PASS] 通过" if result else "[FAIL] 失败"
        log(f"{tc}: {status}")
    
    log(f"总计: {passed}/{total} 通过")
    
    # 保存汇总结果
    summary_file = os.path.join(TEST_DIR, "test-summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_suite": "Storyline 1",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "passed": passed,
            "total": total,
            "pass_rate": f"{passed/total*100:.1f}%"
        }, f, indent=2, ensure_ascii=False)
    
    log(f"汇总结果已保存至: {summary_file}")

if __name__ == "__main__":
    main()
