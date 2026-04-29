"""
TemplateLoader v2 单元测试

覆盖：
1. 文件指纹比对（mtime/size 不变则跳过）
2. 删除文件检测（文件删除后清理 Redis 和缓存）
3. 定时轮询基本功能
"""
import asyncio
import os
import sys
import tempfile
import time
import yaml
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# 在导入前 mock agent_provisioner 的 Skill Loader
sys.modules.setdefault('app.core.agent_provisioner', MagicMock())

from app.core.template_loader import TemplateLoader


@pytest.fixture
def temp_template_dir():
    """创建临时模板目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def loader(temp_template_dir):
    """创建 TemplateLoader 实例"""
    with patch('app.core.template_loader.redis_client') as mock_redis:
        mock_redis.is_connected.return_value = True
        mock_redis.connect.return_value = True
        mock_redis.keys.return_value = []
        loader = TemplateLoader(template_dir=temp_template_dir)
        loader._redis_mock = mock_redis
        yield loader


def _write_template(path, template_id="test-tpl", version="1.0.0"):
    """写入一个最小模板文件"""
    data = {
        "template_id": template_id,
        "version": version,
        "description": "Test template",
        "tasks": [
            {
                "task_id": "task-1",
                "name": "Task 1",
                "type": "fixed",
                "dependencies": [],
                "target_role": "executor",
                "execution_context": {"instruction": "Do something"}
            }
        ]
    }
    with open(path, 'w') as f:
        yaml.dump(data, f)
    return data


# ── 测试 1: 文件指纹比对 ────────────────────────────────────

@pytest.mark.asyncio
async def test_fingerprint_unchanged_skips_reload(loader, temp_template_dir):
    """文件未变更时不应重新加载"""
    tpl_path = os.path.join(temp_template_dir, "test.yaml")
    _write_template(tpl_path)

    await loader._load_all_existing()
    assert "test-tpl" in loader._templates
    assert tpl_path in loader._fingerprints

    first_fp = loader._fingerprints[tpl_path]
    await loader._check_and_reload()

    assert loader._fingerprints[tpl_path] == first_fp
    assert len(loader._templates) == 1


@pytest.mark.asyncio
async def test_fingerprint_changed_triggers_reload(loader, temp_template_dir):
    """文件变更后应触发重新加载"""
    tpl_path = os.path.join(temp_template_dir, "test.yaml")
    _write_template(tpl_path, version="1.0.0")

    await loader._load_all_existing()
    assert loader._templates["test-tpl"].version == "1.0.0"

    time.sleep(0.1)
    _write_template(tpl_path, version="1.0.1")

    await loader._check_and_reload()
    assert loader._templates["test-tpl"].version == "1.0.1"


# ── 测试 2: 删除文件检测 ─────────────────────────────────────

@pytest.mark.asyncio
async def test_deleted_file_cleanup(loader, temp_template_dir):
    """文件删除后应清理 Redis 和缓存"""
    tpl_path = os.path.join(temp_template_dir, "test.yaml")
    _write_template(tpl_path, template_id="test")  # template_id 与文件名一致

    await loader._load_all_existing()
    assert "test" in loader._templates
    assert tpl_path in loader._fingerprints

    os.remove(tpl_path)
    await loader._check_and_reload()

    assert "test" not in loader._templates
    assert tpl_path not in loader._fingerprints
    loader._redis_mock.delete.assert_called_with("template:test")


@pytest.mark.asyncio
async def test_deleted_file_yml_extension(loader, temp_template_dir):
    """删除 .yml 文件也应正确清理"""
    tpl_path = os.path.join(temp_template_dir, "my-tpl.yml")
    _write_template(tpl_path, template_id="my-tpl")

    await loader._load_all_existing()
    assert "my-tpl" in loader._templates

    os.remove(tpl_path)
    await loader._check_and_reload()

    assert "my-tpl" not in loader._templates


# ── 测试 3: 新文件检测 ───────────────────────────────────────

@pytest.mark.asyncio
async def test_new_file_detected(loader, temp_template_dir):
    """新文件应被检测并加载"""
    await loader._load_all_existing()
    assert len(loader._templates) == 0

    tpl_path = os.path.join(temp_template_dir, "new.yaml")
    _write_template(tpl_path, template_id="new-tpl")

    await loader._check_and_reload()
    assert "new-tpl" in loader._templates
    assert tpl_path in loader._fingerprints


# ── 测试 4: 异常处理 ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_yaml_skipped(loader, temp_template_dir):
    """无效 YAML 文件应被跳过"""
    tpl_path = os.path.join(temp_template_dir, "bad.yaml")
    with open(tpl_path, 'w') as f:
        f.write("{{invalid yaml:::")

    result = await loader._load_template(tpl_path)
    assert result is False
    assert len(loader._templates) == 0


@pytest.mark.asyncio
async def test_empty_yaml_skipped(loader, temp_template_dir):
    """空 YAML 文件应被跳过"""
    tpl_path = os.path.join(temp_template_dir, "empty.yaml")
    with open(tpl_path, 'w') as f:
        f.write("")

    result = await loader._load_template(tpl_path)
    assert result is False


@pytest.mark.asyncio
async def test_missing_required_fields_skipped(loader, temp_template_dir):
    """缺少必需字段的模板应被跳过"""
    tpl_path = os.path.join(temp_template_dir, "incomplete.yaml")
    with open(tpl_path, 'w') as f:
        yaml.dump({"template_id": "incomplete"}, f)

    result = await loader._load_template(tpl_path)
    assert result is False


# ── 测试 5: Agent 供给非阻塞 ─────────────────────────────────

@pytest.mark.asyncio
async def test_agent_provisioning_non_blocking(loader, temp_template_dir):
    """Agent 供给应作为后台任务，不阻塞模板加载"""
    tpl_path = os.path.join(temp_template_dir, "test.yaml")
    _write_template(tpl_path)

    with patch('app.core.template_loader.agent_provisioner') as mock_prov:
        mock_prov.ensure_role_exists = AsyncMock(side_effect=Exception("fail"))

        result = await loader._load_template(tpl_path)
        assert result is True
        assert "test-tpl" in loader._templates

        await asyncio.sleep(0.2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
