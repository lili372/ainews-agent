"""缓存工具模块"""
import diskcache
from pathlib import Path
from typing import Optional, Any
import json
from datetime import datetime


class NewsCache:
    """新闻缓存管理器"""

    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 1):
        """初始化缓存

        Args:
            cache_dir: 缓存目录
            ttl_hours: 缓存有效期（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = diskcache.Cache(str(self.cache_dir))
        self.ttl_seconds = ttl_hours * 3600

    def get(self, key: str) -> Optional[Any]:
        """获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期返回None
        """
        value = self.cache.get(key)
        if value is None:
            return None

        try:
            data = json.loads(value)
            cached_time = datetime.fromisoformat(data["timestamp"])
            elapsed = (datetime.now() - cached_time).total_seconds()

            if elapsed > self.ttl_seconds:
                self.cache.delete(key)
                return None

            return data["value"]
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存

        Args:
            key: 缓存键
            value: 缓存值
        """
        data = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.cache.set(key, json.dumps(data, ensure_ascii=False, default=str))

    def delete(self, key: str) -> None:
        """删除缓存"""
        self.cache.delete(key)

    def clear(self) -> None:
        """清空所有缓存"""
        self.cache.clear()

    def exists(self, key: str) -> bool:
        """检查缓存是否存在且未过期"""
        return self.get(key) is not None
