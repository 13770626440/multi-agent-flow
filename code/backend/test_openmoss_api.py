import requests
import json
import sys
import uuid

BASE_URL = "http://localhost:6565"
# PLANNER_KEY = "ak_2c63d655a5cbe811d538c27653806085" # 可能已失效
REG_TOKEN = "maf-register-token-2026"

def log(step, method, url, payload=None, response=None):
    print(f"\n{'='*60}")
    print(f"STEP {step}: {method} {url}")
    if payload:
        print(f"REQUEST BODY:\n{json.dumps(payload, indent=2)}")
    if response is not None:
        print(f"RESPONSE STATUS: {response.status_code}")
        try:
            print(f"RESPONSE BODY:\n{json.dumps(response.json(), indent=2)}")
        except:
            print(f"RESPONSE TEXT: {response.text}")
    print(f"{'='*60}")

def run_tests():
    # 1. 注册 Planner Agent
    print("\n>>> 1. 注册 Planner Agent")
    planner_name = f"plan_{uuid.uuid4().hex[:8]}"
    resp = requests.post(
        f"{BASE_URL}/api/agents/register",
        headers={"X-Registration-Token": REG_TOKEN, "Content-Type": "application/json"},
        json={"name": planner_name, "role": "planner"}
    )
    log(1, "POST", "/api/agents/register (Planner)", response=resp)
    if resp.status_code != 200:
        print("[FAIL] Planner 注册失败"); return
    planner_key = resp.json().get("api_key")
    
    headers_planner = {
        "X-Agent-Key": planner_key,
        "Authorization": f"Bearer {planner_key}",
        "Content-Type": "application/json"
    }

    # 2. 注册 Executor Agent
    print("\n>>> 2. 注册 Executor Agent (验证角色定义)")
    resp = requests.post(
        f"{BASE_URL}/api/agents/register",
        headers={"X-Registration-Token": REG_TOKEN, "Content-Type": "application/json"},
        json={"name": f"exec_{uuid.uuid4().hex[:8]}", "role": "executor"}
    )
    log(2, "POST", "/api/agents/register (Executor)", response=resp)
    if resp.status_code != 200:
        print("[FAIL] 注册失败，测试终止"); return
    
    executor_data = resp.json()
    executor_key = executor_data.get("api_key")
    executor_id = executor_data.get("id")
    if not executor_id: executor_id = executor_data.get("agent_id")
    
    headers_executor = {
        "X-Agent-Key": executor_key,
        "Authorization": f"Bearer {executor_key}",
        "Content-Type": "application/json"
    }

    # 3. 创建父任务 (模拟 Backend 实例化模板)
    print("\n>>> 3. 创建父任务 (模拟模板实例化)")
    task_payload = {
        "name": "测试父任务-数据收集",
        "description": "这是一个父任务，用于包含子任务",
        "type": "once"
    }
    resp = requests.post(f"{BASE_URL}/api/tasks", headers=headers_planner, json=task_payload)
    log(3, "POST", "/api/tasks", task_payload, resp)
    if resp.status_code != 200:
        print("[FAIL] 创建父任务失败，测试终止"); return
    
    parent_task_id = resp.json().get("id")

    # 4. 创建子任务 (验证执行方法和角色绑定)
    print("\n>>> 4. 创建子任务 (验证 execution_context 和 target_role)")
    # 方案验证点：将 execution_context 注入 description，指定 assigned_agent
    sub_task_payload = {
        "task_id": parent_task_id,
        "name": "子任务-执行数据分析",
        "description": "【执行方法】请使用 Python 分析附件数据，输出图表。\n【输入数据】data.csv\n【输出要求】JSON 格式",
        "deliverable": "数据分析报告",
        "acceptance": "包含至少 3 个图表",
        "assigned_agent": executor_id, # 验证角色绑定
        "type": "once"
    }
    resp = requests.post(f"{BASE_URL}/api/sub-tasks", headers=headers_planner, json=sub_task_payload)
    log(4, "POST", "/api/sub-tasks", sub_task_payload, resp)
    if resp.status_code != 200:
        print("[FAIL] 创建子任务失败，测试终止"); return
    
    sub_task_id = resp.json().get("id")

    # 5. Agent 开始任务 (Start) - 跳过 Claim 因为创建时已 assigned
    print("\n>>> 5. Agent 开始任务 (Start)")
    resp = requests.post(f"{BASE_URL}/api/sub-tasks/{sub_task_id}/start", headers=headers_executor)
    log(5, "POST", f"/api/sub-tasks/{sub_task_id}/start", response=resp)
    if resp.status_code != 200:
        print("[FAIL] 开始任务失败"); return

    # 6. Agent 提交结果 (Submit - 验证结果回写)
    print("\n>>> 6. Agent 提交结果 (Submit)")
    # 注意：OpenMOSS submit 接口可能不需要 body，或者 body 包含结果
    submit_payload = {
        "deliverable_content": "这里是执行结果：\n1. 图表 A 已生成\n2. 数据分析完成..."
    }
    # 尝试带 body 提交
    resp = requests.post(f"{BASE_URL}/api/sub-tasks/{sub_task_id}/submit", headers=headers_executor, json=submit_payload)
    # 如果 405 或 400，尝试不带 body
    if resp.status_code in [400, 405, 422]:
        print("⚠️ 带 Body 提交失败，尝试无 Body 提交...")
        resp = requests.post(f"{BASE_URL}/api/sub-tasks/{sub_task_id}/submit", headers=headers_executor)
    
    log(6, "POST", f"/api/sub-tasks/{sub_task_id}/submit", submit_payload, resp)

    # 7. 验证数据持久化
    print("\n>>> 7. 验证数据持久化 (Query)")
    resp = requests.get(f"{BASE_URL}/api/sub-tasks/{sub_task_id}", headers=headers_planner)
    log(7, "GET", f"/api/sub-tasks/{sub_task_id}", response=resp)

    print("\n[PASS] 验证流程执行完毕，请查看上方日志。")

if __name__ == "__main__":
    run_tests()
