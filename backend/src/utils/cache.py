import hashlib
from typing import Optional, Any
from datetime import timedelta
from flask import current_app
import redis

class CacheManager:
    def __init__(self):
        self.client = None
    
    def init_app(self, app):
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        self.client = redis.from_url(redis_url)
    
    def get(self, key: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            return self.client.get(key)
        except Exception:
            return None
    
    def set(self, key: str, value: str, expire: timedelta = timedelta(hours=1)) -> bool:
        if not self.client:
            return False
        try:
            self.client.set(key, value, ex=expire)
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False
    
    def generate_key(self, data: bytes) -> str:
        return hashlib.md5(data).hexdigest()

cache_manager = CacheManager()