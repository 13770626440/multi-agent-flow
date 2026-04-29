"""
模板加载器

负责监控 templates/ 目录，自动加载 YAML 模板文件，进行校验后存入 Redis 缓存。
并在加载成功后触发 Agent 动态供给机制。
"""
import os
import time
import yaml
import json
import asyncio
import logging
from typing import Dict, Optional
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from app.schemas.template import TemplateSchema
from app.core.redis_client import redis_client
from app.core.agent_provisioner import agent_provisioner
from app.config import get_settings

logger = logging.getLogger(__name__)


class TemplateFileHandler(FileSystemEventHandler):
    """文件变更处理器"""
    
    def __init__(self, loader: 'TemplateLoader', debounce_seconds: float = 1.0):
        self.loader = loader
        self.debounce_seconds = debounce_seconds  # 防抖动时间（配置化）
        self._last_modified: Dict[str, float] = {}
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if not (file_path.endswith('.yaml') or file_path.endswith('.yml')):
            return
        
        # 防抖动处理：使用配置的防抖动时间
        current_time = time.time()
        if file_path in self._last_modified and (current_time - self._last_modified[file_path]) < self.debounce_seconds:
            return
        
        self._last_modified[file_path] = current_time
        
        # ARCH-012 修复：使用线程池延迟处理，避免阻塞 Watchdog 线程
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        executor.submit(self._delayed_load, file_path)
    
    def _delayed_load(self, file_path: str):
        """延迟加载模板（ARCH-012 修复）"""
        time.sleep(0.5)  # 在线程中 sleep，不阻塞 Watchdog
        self.loader.load_template(file_path)
    
    def on_created(self, event):
        self.on_modified(event)


class TemplateLoader:
    """模板加载器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        settings = get_settings()
        self.template_dir = template_dir or settings.TEMPLATE_DIR
        self.debounce_seconds = settings.TEMPLATE_DEBOUNCE_SECONDS  # 从配置读取防抖动时间
        self.observer = PollingObserver(timeout=1.0)  # 轮询间隔 1 秒，适配 Docker 9p 文件系统
        self.handler = TemplateFileHandler(self, self.debounce_seconds)
        self._templates: Dict[str, TemplateSchema] = {}  # 本地缓存
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None  # 保存主事件循环引用
    
    def start(self, event_loop: Optional[asyncio.AbstractEventLoop] = None) -> bool:
        """启动加载器
        
        Args:
            event_loop: 主事件循环引用（用于在 Watchdog 线程中调度异步任务）
        """
        # 保存主事件循环引用
        if event_loop:
            self._event_loop = event_loop
            logger.info("Main event loop reference saved")
        
        # 确保 Redis 连接
        if not redis_client.is_connected():
            if not redis_client.connect():
                logger.error("Redis connection failed, template loader cannot start")
                return False
        
        # 确保模板目录存在
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            logger.info(f"Created template directory: {self.template_dir}")
        
        # 启动文件监控
        self.observer.schedule(self.handler, self.template_dir, recursive=False)
        self.observer.start()
        logger.info(f"TemplateLoader started, watching {self.template_dir}")
        
        # 加载现有模板
        self.load_all_existing()
        return True
    
    def stop(self):
        """停止加载器"""
        self.observer.stop()
        self.observer.join()
        redis_client.disconnect()
        logger.info("TemplateLoader stopped")
    
    def load_all_existing(self) -> int:
        """加载所有现有模板"""
        count = 0
        if not os.path.exists(self.template_dir):
            return count
        
        for filename in os.listdir(self.template_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                file_path = os.path.join(self.template_dir, filename)
                if self.load_template(file_path):
                    count += 1
        
        logger.info(f"Loaded {count} existing templates")
        return count
    
    def load_template(self, file_path: str) -> bool:
        """加载单个模板文件（同步方法，用于 Watchdog 回调）"""
        try:
            logger.info(f"Loading template from {file_path}")
            
            # 读取 YAML 文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"YAML file is empty: {file_path}")
                return False
            
            # 设置时间戳（ARCH-S2-001 修复：保持 datetime 类型，让 Pydantic 自动处理序列化）
            from datetime import datetime
            now = datetime.now()
            data['created_at'] = now
            data['updated_at'] = now
            
            # Schema 校验（包含 DAG 循环检测）
            template = TemplateSchema(**data)
            
            # 存入 Redis
            # ARCH-S2-001 修复：使用 mode='json' 确保 datetime 等特殊类型被序列化为 JSON 兼容格式
            redis_key = f"template:{template.template_id}"
            template_data = template.model_dump(mode='json')
            
            if redis_client.set(redis_key, template_data):
                self._templates[template.template_id] = template
                logger.info(f"Template {template.template_id} v{template.version} loaded successfully")
                
                # 触发 Agent 动态供给（异步）
                self._trigger_agent_provisioning(template_data)
                
                return True
            else:
                logger.error(f"Failed to save template to Redis: {template.template_id}")
                return False
            
        except yaml.YAMLError as e:
            logger.error(f"YAML syntax error in {file_path}: {e}")
            return False
        except ValueError as e:
            logger.error(f"Template validation error in {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load template {file_path}: {e}")
            return False

    def _trigger_agent_provisioning(self, template_data: Dict):
        """
        触发 Agent 动态供给。
        使用 run_coroutine_threadsafe() 安全地在 Watchdog 线程中调度异步任务到主事件循环。
        """
        roles = template_data.get("roles", {})
        if not roles:
            logger.info("No roles defined in template, skipping agent provisioning")
            return

        if not self._event_loop:
            logger.warning("No event loop reference available, cannot trigger agent provisioning")
            return

        try:
            for role_name, config in roles.items():
                model = config.get("model", "qwen3.6-plus")
                logger.info(f"Scheduling agent provisioning for role: {role_name} (model: {model})")
                
                # 使用 run_coroutine_threadsafe 安全地调度到主事件循环
                future = asyncio.run_coroutine_threadsafe(
                    agent_provisioner.ensure_role_exists(role_name, model),
                    self._event_loop
                )
                
                # 添加回调以记录结果
                def _on_done(f, role=role_name):
                    try:
                        result = f.result()
                        logger.info(f"Agent provisioning completed for role '{role}': {result}")
                    except Exception as e:
                        logger.error(f"Agent provisioning failed for role '{role}': {e}")
                
                future.add_done_callback(_on_done)
                
        except Exception as e:
            logger.error(f"Failed to schedule agent provisioning: {e}")
    
    def get_template(self, template_id: str) -> Optional[TemplateSchema]:
        """获取模板"""
        # 先查本地缓存
        if template_id in self._templates:
            return self._templates[template_id]
        
        # 查 Redis
        redis_key = f"template:{template_id}"
        data = redis_client.get(redis_key)
        if data:
            try:
                template = TemplateSchema(**data)
                self._templates[template_id] = template
                return template
            except Exception as e:
                logger.error(f"Failed to parse template from Redis: {e}")
        
        return None
    
    def list_templates(self) -> list:
        """获取所有模板ID列表"""
        keys = redis_client.keys("template:*")
        return [k.replace("template:", "") for k in keys]
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        redis_key = f"template:{template_id}"
        if redis_client.delete(redis_key):
            if template_id in self._templates:
                del self._templates[template_id]
            logger.info(f"Template {template_id} deleted")
            return True
        return False