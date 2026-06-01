from database.database import SessionLocal
from database.models.user_memories import UserMemory


def create_user_memory(
    user_id: str,
    memory_type: str,
    content: str,
    source_workflow_id: str | None = None,
):
    db = SessionLocal()

    try:
        memory = UserMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            source_workflow_id=source_workflow_id,
        )

        db.add(memory)
        db.commit()
        db.refresh(memory)

        return memory

    finally:
        db.close()


def upsert_user_memory(
    user_id: str,
    memory_type: str,
    content: str,
    source_workflow_id: str | None = None,
):
    db = SessionLocal()

    try:
        memory = (
            db.query(UserMemory)
            .filter(
                UserMemory.user_id == user_id,
                UserMemory.memory_type == memory_type,
            )
            .first()
        )

        if memory:
            memory.content = content
            memory.source_workflow_id = source_workflow_id
        else:
            memory = UserMemory(
                user_id=user_id,
                memory_type=memory_type,
                content=content,
                source_workflow_id=source_workflow_id,
            )
            db.add(memory)

        db.commit()
        db.refresh(memory)

        return memory

    finally:
        db.close()


def list_user_memories(
    user_id: str,
    memory_type: str | None = None,
    limit: int = 5,
):
    db = SessionLocal()

    try:
        query = db.query(UserMemory).filter(UserMemory.user_id == user_id)

        if memory_type:
            query = query.filter(UserMemory.memory_type == memory_type)

        return query.order_by(UserMemory.updated_at.desc()).limit(limit).all()

    finally:
        db.close()
