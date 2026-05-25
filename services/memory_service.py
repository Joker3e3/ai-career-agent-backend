import json
import logging

from redis.exceptions import RedisError

from services.redis_service import REDIS_HOST, REDIS_PORT, redis_client


logger = logging.getLogger(__name__)


class MemoryService:

    def __init__(self):
        self.prefix = "career_agent:memory"

    def _build_key(self, session_id: str):

        return f"{self.prefix}:{session_id}"

    def save_memory(
        self,
        session_id: str,
        memory: dict
    ):
        if redis_client is None:
            logger.warning("Redis memory is disabled; skipping save.")
            return

        key = self._build_key(session_id)

        try:
            redis_client.lpush(
                key,
                json.dumps(memory, ensure_ascii=False)
            )
            redis_client.ltrim(key, 0, 4)
        except RedisError as exc:
            logger.warning(
                "Redis unavailable at %s:%s; skipping memory save: %s",
                REDIS_HOST,
                REDIS_PORT,
                exc,
            )

    def get_memories(
        self,
        session_id: str
    ):
        if redis_client is None:
            logger.warning("Redis memory is disabled; returning empty history.")
            return []

        key = self._build_key(session_id)

        try:
            memories = redis_client.lrange(
                key,
                0,
                -1
            )
        except RedisError as exc:
            logger.warning(
                "Redis unavailable at %s:%s; returning empty history: %s",
                REDIS_HOST,
                REDIS_PORT,
                exc,
            )
            return []

        return [
            json.loads(item)
            for item in memories
        ]
