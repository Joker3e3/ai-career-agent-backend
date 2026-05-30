import json
import os
import logging

from redis.exceptions import RedisError

from config.settings import SESSION_MEMORY_TTL
from services.redis_service import REDIS_HOST, REDIS_PORT, redis_client

logger = logging.getLogger(__name__)


# session级memory，仅保存最近五轮对话的分析结果，存于Redis
class SessionMemoryService:

    def __init__(self):
        self.prefix = "career_agent:session_memory"
        self.ttl_seconds = SESSION_MEMORY_TTL

    def _build_key(self, user_id: str, session_id: str):

        return f"{self.prefix}:{user_id}:{session_id}"

    def save_memory(self, user_id: str, session_id: str, memory: dict):
        if redis_client is None:
            logger.warning("Redis memory is disabled; skipping save.")
            return

        key = self._build_key(user_id=user_id, session_id=session_id)

        try:
            redis_client.lpush(key, json.dumps(memory, ensure_ascii=False, default=str))
            redis_client.ltrim(key, 0, 4)
            redis_client.expire(key, self.ttl_seconds)
        except RedisError as exc:
            logger.warning(
                "Redis unavailable at %s:%s; skipping memory save: %s",
                REDIS_HOST,
                REDIS_PORT,
                exc,
            )

    def get_memories(self, user_id: str, session_id: str):
        if redis_client is None:
            logger.warning("Redis memory is disabled; returning empty history.")
            return []

        key = self._build_key(user_id=user_id, session_id=session_id)

        try:
            memories = redis_client.lrange(key, 0, -1)
        except RedisError as exc:
            logger.warning(
                "Redis unavailable at %s:%s; returning empty history: %s",
                REDIS_HOST,
                REDIS_PORT,
                exc,
            )
            return []

        return [json.loads(item) for item in memories]
