import json
import os
from services.redis_service import redis_client


class WorkflowStateService:
    def __init__(self):
        self.prefix = "career_agent:workflow"
        self.ttl_seconds = int(os.getenv("WORKFLOW_STATE_TTL_SECONDS", 60 * 60 * 24))

    def _build_key(self, workflow_id: str):
        return f"{self.prefix}:{workflow_id}"

    def save_state(self, workflow_id: str, state: dict):
        key = self._build_key(workflow_id)

        redis_client.set(
            key, json.dumps(state, ensure_ascii=False), ex=self.ttl_seconds
        )

    def get_state(self, workflow_id: str):
        key = self._build_key(workflow_id)
        data = redis_client.get(key)

        if not data:
            return None

        return json.loads(data)

    def update_state(self, workflow_id: str, updates: dict):
        state = self.get_state(workflow_id)

        if not state:
            return None

        state.update(updates)

        self.save_state(workflow_id=workflow_id, state=state)

        return state

    def delete_state(self, workflow_id: str):
        key = self._build_key(workflow_id)
        redis_client.delete(key)
