import json
import os
from config.settings import CONFIRMATION_TTL
from services.redis_service import redis_client


class ConfirmationService:
    def __init__(self):
        self.prefix = "career_agent:confirmation"
        # self.ttl_seconds = CONFIRMATION_TTL

    def _build_key(self, confirmation_id: str):
        return f"{self.prefix}:{confirmation_id}"

    def save_confirmation(self, confirmation_id: str, data: dict):
        redis_client.set(
            self._build_key(confirmation_id),
            json.dumps(data, ensure_ascii=False),
            # ex=self.ttl_seconds,
        )

    def get_confirmation(self, confirmation_id: str):
        data = redis_client.get(self._build_key(confirmation_id))

        if not data:
            return None

        return json.loads(data)

    def update_confirmation(self, confirmation_id: str, updates: dict):
        confirmation = self.get_confirmation(confirmation_id)

        if not confirmation:
            return None

        confirmation.update(updates)

        self.save_confirmation(confirmation_id=confirmation_id, data=confirmation)

        return confirmation
