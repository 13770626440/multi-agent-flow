"""
模板加载器

通过定时轮询 + 文件指纹 (mtime, size) 快速检测模板变更并自动加载。
加载成功后触发 Agent 动态供给机制。
"""
import os
import yaml
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from app.schemas.template import TemplateSchema
from app.core.redis_client import redis_client
from app.core.agent_provisioner import agent_provisioner
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class TemplateLoader:
    """模板加载器 — 定时轮询 + 文件指纹快速比对"""

    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or settings.TEMPLATE_DIR
        self.check_interval = getattr(settings, 'TEMPLATE_CHECK_INTERVAL_SECONDS', 15)
        self._templates: Dict[str, TemplateSchema] = {}
        # 文件指纹: {file_path: (mtime, size)}
        self._fingerprints: Dict[str, tuple] = {}
        self._running = False

    # ── 启动 / 停止 ──────────────────────────────────────────

    async def start(self) -> bool:
        """启动：连接 Redis → 首次全量加载 → 启动定时轮询"""
        if not redis_client.is_connected():
            if not redis_client.connect():
                logger.error("Redis connection failed")
                return False

        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)

        count = await self._load_all_existing()
        self._running = True
        asyncio.create_task(self._poll_loop())
        logger.info(f"TemplateLoader started, {count} templates, interval={self.check_interval}s")
        return True

    async def stop(self):
        self._running = False
        logger.info("TemplateLoader stopped")

    # ── 定时轮询 ─────────────────────────────────────────────

    async def _poll_loop(self):
        while self._running:
            try:
                await self._check_and_reload()
            except Exception as e:
                logger.error(f"Poll error: {e}")
            await asyncio.sleep(self.check_interval)

    async def _check_and_reload(self):
        """扫描目录，通过 (mtime, size) 指纹快速比对"""
        if not os.path.exists(self.template_dir):
            return

        current_files = set()
        for filename in os.listdir(self.template_dir):
            if not (filename.endswith('.yaml') or filename.endswith('.yml')):
                continue

            file_path = os.path.join(self.template_dir, filename)
            current_files.add(file_path)

            try:
                stat = os.stat(file_path)
                fingerprint = (stat.st_mtime, stat.st_size)
            except OSError:
                continue

            if self._fingerprints.get(file_path) == fingerprint:
                continue

            logger.info(f"Template changed: {filename}")
            await self._load_template(file_path)
            self._fingerprints[file_path] = fingerprint

        # P2 修复：检测并清理已删除的文件
        deleted = set(self._fingerprints.keys()) - current_files
        for file_path in deleted:
            template_id = self._extract_template_id(file_path)
            if template_id:
                logger.info(f"Template file deleted, cleaning up: {template_id}")
                redis_client.delete(f"template:{template_id}")
                self._templates.pop(template_id, None)
            del self._fingerprints[file_path]

    def _extract_template_id(self, file_path: str) -> Optional[str]:
        """从文件路径提取 template_id"""
        # 先尝试通过文件名匹配已知模板
        for tid, tmpl in self._templates.items():
            if file_path.endswith(f"{tid}.yaml") or file_path.endswith(f"{tid}.yml"):
                return tid
        # 从文件名推断（去掉扩展名）
        basename = os.path.basename(file_path)
        return basename.rsplit('.', 1)[0] if '.' in basename else None

    # ── 模板加载 ─────────────────────────────────────────────

    async def _load_all_existing(self) -> int:
        count = 0
        if not os.path.exists(self.template_dir):
            return count
        for filename in os.listdir(self.template_dir):
            if filename.endswith(('.yaml', '.yml')):
                file_path = os.path.join(self.template_dir, filename)
                if await self._load_template(file_path):
                    # 记录初始指纹
                    try:
                        stat = os.stat(file_path)
                        self._fingerprints[file_path] = (stat.st_mtime, stat.st_size)
                    except OSError:
                        pass
                    count += 1
        return count

    async def _load_template(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning(f"Empty YAML: {file_path}")
                return False

            now = datetime.now()
            data['created_at'] = now
            data['updated_at'] = now

            template = TemplateSchema(**data)
            redis_key = f"template:{template.template_id}"

            if not redis_client.set(redis_key, template.model_dump(mode='json')):
                logger.error(f"Redis write failed: {template.template_id}")
                return False

            self._templates[template.template_id] = template
            logger.info(f"Template {template.template_id} v{template.version} loaded")

            # P1 修复：Agent 供给改为非阻塞后台任务
            asyncio.create_task(self._trigger_agent_provisioning(data))
            return True

        except yaml.YAMLError as e:
            logger.error(f"YAML error {file_path}: {e}")
            return False
        except ValueError as e:
            logger.error(f"Validation error {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Load failed {file_path}: {e}")
            return False

    # ── Agent 供给 ───────────────────────────────────────────

    async def _trigger_agent_provisioning(self, template_data: Dict):
        """P1 修复：异步后台执行，不阻塞模板加载"""
        roles = template_data.get("roles", {})
        if not roles:
            return

        for role_name, config in roles.items():
            model = config.get("model", "qwen3.6-plus")
            try:
                ok = await agent_provisioner.ensure_role_exists(role_name, model)
                logger.info(f"Agent '{role_name}': {'OK' if ok else 'FAIL'}")
            except Exception as e:
                logger.error(f"Agent '{role_name}' error: {e}")

    # ── 查询接口（不变）──────────────────────────────────────

    def get_template(self, template_id: str) -> Optional[TemplateSchema]:
        if template_id in self._templates:
            return self._templates[template_id]
        data = redis_client.get(f"template:{template_id}")
        if data:
            try:
                t = TemplateSchema(**data)
                self._templates[template_id] = t
                return t
            except Exception as e:
                logger.error(f"Parse error: {e}")
        return None

    def list_templates(self) -> list:
        return [k.replace("template:", "") for k in redis_client.keys("template:*")]

    def delete_template(self, template_id: str) -> bool:
        if redis_client.delete(f"template:{template_id}"):
            self._templates.pop(template_id, None)
            return True
        return False
