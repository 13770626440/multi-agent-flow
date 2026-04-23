"""
Redis 客户端封装

用于存储模板定义、运行中 DAG 状态、配置缓存。
"""
import redis
import json
import logging
from typing import Optional, Any
from app.config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 客户端封装类"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            self._client = redis.Redis(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                db=self.settings.REDIS_DB,
                password=self.settings.REDIS_PASSWORD,
                decode_responses=True,
                max_connections=self.settings.REDIS_MAX_CONNECTIONS  # 连接池配置
            )
            # 测试连接
            self._client.ping()
            logger.info(f"Redis connected: {self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}")
            return True
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            self._client = None
            return False
    
    def disconnect(self):
        """断开连接"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis disconnected")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except redis.ConnectionError:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取值"""
        if not self._client:
            logger.warning(f"Redis not connected, cannot get key: {key}")
            return None
        try:
            value = self._client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except redis.RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置值"""
        if not self._client:
            logger.warning(f"Redis not connected, cannot set key: {key}")
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            if ttl:
                self._client.setex(key, ttl, value)
            else:
                self._client.set(key, value)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除键"""
        if not self._client:
            logger.warning(f"Redis not connected, cannot delete key: {key}")
            return False
        try:
            self._client.delete(key)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._client:
            return False
        try:
            return self._client.exists(key) > 0
        except redis.RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    def keys(self, pattern: str) -> list:
        """获取匹配模式的键列表"""
        if not self._client:
            return []
        try:
            return self._client.keys(pattern)
        except redis.RedisError as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []


# 全局单例
redis_client = RedisClient()