"""
Agent 注册脚本

功能：
1. 注册 planner、executor、reviewer、patrol 角色到 OpenMOSS
2. 将 API Key 写入 .env 文件
3. 支持幂等性检查、重试、dry-run 模式

使用方式：
    python scripts/register_agents.py                  # 正常注册
    python scripts/register_agents.py --dry-run        # 仅验证不注册
    python scripts/register_agents.py --force          # 强制重新注册
"""
import os
import sys
import asyncio
import httpx
import argparse
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv, set_key, find_dotenv

# 加载 .env 文件
load_dotenv()

# 配置
OPENMOSS_BASE_URL = os.getenv("OPENMOSS_BASE_URL", "http://openmoss:6565")
REGISTRATION_TOKEN = os.getenv("OPENMOSS_REGISTRATION_TOKEN", "default-registration-token")

# 需要注册的角色
ROLES = ["planner", "executor", "reviewer", "patrol"]


async def register_agent(name: str, role: str, description: str, force: bool = False) -> Dict:
    """注册单个 Agent

    幂等性策略：直接注册，捕获 400 错误识别已存在 Agent。
    不再使用 check_agent_exists 预检（会导致鉴权死锁）。
    """
    # 2. 注册 Agent（带重试）
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OPENMOSS_BASE_URL}/api/agents/register",
                    headers={"X-Registration-Token": REGISTRATION_TOKEN},
                    json={
                        "name": name,
                        "role": role,
                        "description": description
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400:
                    print(f"⚠️  Agent 已存在：{name}")
                    return await check_agent_exists(name) or {}
                else:
                    print(f"❌ 注册失败：{response.status_code} - {response.text}")
                    
        except httpx.ConnectError as e:
            print(f"⚠️  连接失败（{attempt + 1}/{max_retries}）：{e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
    
    return {}


def save_to_env(api_key: str, role: str) -> None:
    """保存 API Key 到 .env 文件"""
    env_file = find_dotenv()
    if not env_file:
        env_file = ".env"
        Path(env_file).touch()
    
    key_name = f"OPENMOSS_{role.upper()}_TOKEN"
    set_key(env_file, key_name, api_key)
    print(f"💾 已保存 {key_name} 到 .env")


async def main():
    parser = argparse.ArgumentParser(description="注册 OpenMOSS Agent")
    parser.add_argument("--dry-run", action="store_true", help="仅验证不实际注册")
    parser.add_argument("--force", action="store_true", help="强制重新注册")
    args = parser.parse_args()
    
    print(f"🚀 开始注册 Agent 到 {OPENMOSS_BASE_URL}")
    print(f"📝 角色列表：{', '.join(ROLES)}")
    print()
    
    if args.dry_run:
        print("🔍 Dry-run 模式：仅验证连接")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{OPENMOSS_BASE_URL}/api/health")
                if response.status_code == 200:
                    print("✅ OpenMOSS 连接正常")
                else:
                    print(f"❌ OpenMOSS 返回 {response.status_code}")
                    sys.exit(1)
            except Exception as e:
                print(f"❌ 无法连接 OpenMOSS：{e}")
                sys.exit(1)
        return
    
    # 注册所有角色
    for role in ROLES:
        name = f"{role}-001"
        description = f"{role.capitalize()} agent for multi-agent-flow"
        
        print(f"📝 注册 {name}...")
        try:
            result = await register_agent(name, role, description, force=args.force)
            if result and result.get("api_key"):
                save_to_env(result["api_key"], role)
                print(f"✅ {name} 注册成功")
            else:
                print(f"⚠️  {name} 注册失败或已存在")
        except Exception as e:
            print(f"❌ {name} 注册失败：{e}")
    
    print()
    print("🎉 注册完成！请检查 .env 文件中的 API Key")


if __name__ == "__main__":
    asyncio.run(main())
