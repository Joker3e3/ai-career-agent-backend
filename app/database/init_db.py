from app.database.database import engine, Base

# 导入所有 model
from app.database.models.agent_run import AgentRun
from app.database.models.human_confirmation import HumanConfirmation


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()