from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings


class Cache:
    def __init__(self) -> None:
        self.redis: Redis | None = None
        self.memory: dict[str, tuple[float, str]] = {}
        self.memory_counters: defaultdict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))

    async def connect(self) -> None:
        try:
            client = Redis.from_url(settings.redis_url, decode_responses=True)
            await client.ping()
            self.redis = client
        except Exception:
            self.redis = None

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()
            self.redis = None

    async def get_json(self, key: str) -> Any | None:
        value: str | None = None
        if self.redis is not None:
            try:
                value = await self.redis.get(key)
            except Exception:
                self.redis = None
        if value is None:
            item = self.memory.get(key)
            if item and item[0] > time.time():
                value = item[1]
            elif item:
                self.memory.pop(key, None)
        return json.loads(value) if value else None

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        raw = json.dumps(value, ensure_ascii=False, default=str)
        if self.redis is not None:
            try:
                await self.redis.set(key, raw, ex=ttl_seconds)
                return
            except Exception:
                self.redis = None
        self.memory[key] = (time.time() + ttl_seconds, raw)

    async def delete(self, key: str) -> None:
        self.memory.pop(key, None)
        if self.redis is not None:
            try:
                await self.redis.delete(key)
            except Exception:
                self.redis = None

    async def increment_window(self, key: str, ttl_seconds: int) -> int:
        if self.redis is not None:
            try:
                value = await self.redis.incr(key)
                if value == 1:
                    await self.redis.expire(key, ttl_seconds)
                return int(value)
            except Exception:
                self.redis = None
        count, expires = self.memory_counters[key]
        now = time.time()
        if expires <= now:
            count, expires = 0, now + ttl_seconds
        count += 1
        self.memory_counters[key] = (count, expires)
        return count

    async def acquire_lock(self, key: str, ttl_seconds: int) -> bool:
        if self.redis is not None:
            try:
                return bool(await self.redis.set(key, "1", ex=ttl_seconds, nx=True))
            except Exception:
                self.redis = None
        existing = self.memory.get(key)
        if existing and existing[0] > time.time():
            return False
        self.memory[key] = (time.time() + ttl_seconds, "1")
        return True

    @property
    def backend_name(self) -> str:
        return "redis" if self.redis is not None else "memory"


cache = Cache()
