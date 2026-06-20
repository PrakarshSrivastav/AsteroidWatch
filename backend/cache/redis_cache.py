import os
import json
import logging
from typing import Optional, Any
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RedisCache")

class RedisCache:
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.enabled = True
        self._in_memory_fallback = {}
        
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                socket_timeout=2.0,
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Connected to Redis cache at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            self.enabled = False
            logger.warning(f"Could not connect to Redis cache at {self.redis_host}:{self.redis_port}. Falling back to In-Memory cache. Error: {e}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if self.enabled and self.client:
            try:
                data = self.client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error for key '{key}': {e}. Falling back to in-memory.")
        
        return self._in_memory_fallback.get(key)

    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        serialized = json.dumps(value)
        
        self._in_memory_fallback[key] = value
        
        if self.enabled and self.client:
            try:
                self.client.setex(key, expire_seconds, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error for key '{key}': {e}.")
                
        return False

    def delete(self, key: str) -> bool:
        if key in self._in_memory_fallback:
            del self._in_memory_fallback[key]
            
        if self.enabled and self.client:
            try:
                self.client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error for key '{key}': {e}")
                
        return False

cache = RedisCache()
