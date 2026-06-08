import json
import os
from config.settings import WORKFLOW_STATE_TTL
from services.redis_service import redis_client


class WorkflowStateService:
    def __init__(self):
        self.prefix = "career_agent:workflow"
        self.ttl_seconds = WORKFLOW_STATE_TTL

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

workflow_state_service = WorkflowStateService()