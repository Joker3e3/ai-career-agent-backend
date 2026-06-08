import json
from typing import Any

from database.database import SessionLocal
from database.models.workflow_checkpoint import WorkflowCheckpoint
from utils.time import now_utc8


def upsert_workflow_checkpoint(
    workflow_id: str,
    status: str,
    current_node: str,
    checkpoint: dict[str, Any],
):
    db = SessionLocal()

    try:
        checkpoint_record = (
            db.query(WorkflowCheckpoint)
            .filter(WorkflowCheckpoint.workflow_id == workflow_id)
            .first()
        )

        checkpoint_json = json.dumps(
            checkpoint,
            ensure_ascii=False,
        )

        if checkpoint_record:
            checkpoint_record.status = status
            checkpoint_record.current_node = current_node
            checkpoint_record.checkpoint_json = checkpoint_json
            checkpoint_record.updated_at = now_utc8()
        else:
            checkpoint_record = WorkflowCheckpoint(
                workflow_id=workflow_id,
                status=status,
                current_node=current_node,
                checkpoint_json=checkpoint_json,
                created_at=now_utc8(),
                updated_at=now_utc8(),
            )

            db.add(checkpoint_record)

        db.commit()
        db.refresh(checkpoint_record)

        return checkpoint_record

    finally:
        db.close()


def get_workflow_checkpoint(
    workflow_id: str,
) -> dict[str, Any] | None:
    db = SessionLocal()

    try:
        checkpoint_record = (
            db.query(WorkflowCheckpoint)
            .filter(WorkflowCheckpoint.workflow_id == workflow_id)
            .first()
        )

        if not checkpoint_record:
            return None

        return json.loads(checkpoint_record.checkpoint_json)

    finally:
        db.close()


def update_workflow_checkpoint(
    workflow_id: str,
    **updates,
):
    db = SessionLocal()

    try:
        checkpoint_record = (
            db.query(WorkflowCheckpoint)
            .filter(WorkflowCheckpoint.workflow_id == workflow_id)
            .first()
        )

        if not checkpoint_record:
            return None

        for key, value in updates.items():
            if key == "checkpoint" and isinstance(value, dict):
                checkpoint_record.checkpoint_json = json.dumps(
                    value,
                    ensure_ascii=False,
                )
            elif hasattr(checkpoint_record, key):
                setattr(checkpoint_record, key, value)

        checkpoint_record.updated_at = now_utc8()

        db.commit()
        db.refresh(checkpoint_record)

        return checkpoint_record

    finally:
        db.close()


def delete_workflow_checkpoint(
    workflow_id: str,
):
    db = SessionLocal()

    try:
        checkpoint_record = (
            db.query(WorkflowCheckpoint)
            .filter(WorkflowCheckpoint.workflow_id == workflow_id)
            .first()
        )

        if not checkpoint_record:
            return False

        db.delete(checkpoint_record)
        db.commit()

        return True

    finally:
        db.close()