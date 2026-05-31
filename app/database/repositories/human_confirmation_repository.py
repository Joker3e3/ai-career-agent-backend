from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.database.models.human_confirmation import HumanConfirmation


def create_human_confirmation(
    db: Session,
    confirmation_id: str,
    workflow_id: str,
    actor_id: str,
    action_type: str,
    status: str,
    payload_snapshot: str = "",
    user_action: str | None = None,
    message: str | None = None,
):

    confirmation = HumanConfirmation(
        confirmation_id=confirmation_id,
        workflow_id=workflow_id,
        actor_id=actor_id,
        action_type=action_type,
        status=status,
        user_action=user_action,
        payload_snapshot=payload_snapshot,
        message=message,
    )

    db.add(confirmation)
    db.flush()
    db.refresh(confirmation)

    return confirmation


def get_human_confirmation_by_id(confirmation_id: str):
    db = SessionLocal()

    try:
        return (
            db.query(HumanConfirmation)
            .filter(HumanConfirmation.confirmation_id == confirmation_id)
            .first()
        )

    finally:
        db.close()


def update_human_confirmation(
    db: Session,
    confirmation_id: str,
    **updates,
):

    confirmation = (
        db.query(HumanConfirmation)
        .filter(HumanConfirmation.confirmation_id == confirmation_id)
        .first()
    )

    if not confirmation:
        return None

    for key, value in updates.items():
        setattr(confirmation, key, value)

    db.flush()
    db.refresh(confirmation)

    return confirmation
