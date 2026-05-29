from app.database.database import SessionLocal
from app.database.models.human_confirmation import HumanConfirmation


def create_human_confirmation(
    confirmation_id: str,
    workflow_id: str,
    action_type: str,
    status: str,
    user_action: str = "",
    message: str = "",
):
    db = SessionLocal()

    try:
        confirmation = HumanConfirmation(
            confirmation_id=confirmation_id,
            workflow_id=workflow_id,
            action_type=action_type,
            status=status,
            user_action=user_action,
            message=message,
        )

        db.add(confirmation)
        db.commit()
        db.refresh(confirmation)

        return confirmation

    finally:
        db.close()


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
    confirmation_id: str,
    **updates,
):
    db = SessionLocal()

    try:
        confirmation = (
            db.query(HumanConfirmation)
            .filter(HumanConfirmation.confirmation_id == confirmation_id)
            .first()
        )

        if not confirmation:
            return None

        for key, value in updates.items():
            setattr(confirmation, key, value)

        db.commit()
        db.refresh(confirmation)

        return confirmation

    finally:
        db.close()