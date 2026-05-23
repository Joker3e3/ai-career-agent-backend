from services.redis_service import redis_client
import json


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

        key = self._build_key(session_id)

        redis_client.lpush(
            key,
            json.dumps(memory, ensure_ascii=False)
        )

        # 只保留最近 5 条
        redis_client.ltrim(key, 0, 4)

    def get_memories(
        self,
        session_id: str
    ):

        key = self._build_key(session_id)

        memories = redis_client.lrange(
            key,
            0,
            -1
        )

        return [
            json.loads(item)
            for item in memories
        ]