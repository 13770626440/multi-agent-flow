"""
模板加载器

负责监控 templates/ 目录，自动加载 YAML 模板文件，进行校验后存入 Redis 缓存。
"""
import os
import time
import yaml
import json
import logging
from typing import Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.schemas.template import TemplateSchema
from app.core.redis_client import redis_client
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
        
        # 延迟处理，确保文件写入完成
        time.sleep(0.5)
        self.loader.load_template(file_path)
    
    def on_created(self, event):
        self.on_modified(event)


class TemplateLoader:
    """模板加载器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        settings = get_settings()
        self.template_dir = template_dir or settings.TEMPLATE_DIR
        self.debounce_seconds = settings.TEMPLATE_DEBOUNCE_SECONDS  # 从配置读取防抖动时间
        self.observer = Observer()
        self.handler = TemplateFileHandler(self, self.debounce_seconds)
        self._templates: Dict[str, TemplateSchema] = {}  # 本地缓存
    
    def start(self) -> bool:
        """启动加载器"""
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
        """加载单个模板文件"""
        try:
            logger.info(f"Loading template from {file_path}")
            
            # 读取 YAML 文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"YAML file is empty: {file_path}")
                return False
            
            # Schema 校验（包含 DAG 循环检测）
            template = TemplateSchema(**data)
            
            # 存入 Redis
            redis_key = f"template:{template.template_id}"
            template_data = template.model_dump()
            
            if redis_client.set(redis_key, template_data):
                self._templates[template.template_id] = template
                logger.info(f"Template {template.template_id} v{template.version} loaded successfully")
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