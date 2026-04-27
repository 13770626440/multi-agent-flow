import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/test_skill_loader_comprehensive.py", 
     "tests/test_skill_loader_security.py", 
     "-v", "--tb=short"],
    capture_output=True,
    text=True,
    cwd=r"D:\coding\multi-agent-flow\code\backend"
)

print(result.stdout)
print(result.stderr)
print(f"\nExit code: {result.returncode}")

# 统计结果
passed = result.stdout.count("PASSED")
failed = result.stdout.count("FAILED")
errors = result.stdout.count("ERROR")
print(f"\n=== 测试统计 ===")
print(f"通过: {passed}")
print(f"失败: {failed}")
print(f"错误: {errors}")
print(f"总计: {passed + failed + errors}")