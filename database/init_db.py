from database.database import engine, Base

# 导入所有 model
from database.models.agent_run import AgentRun
from database.models.human_confirmation import HumanConfirmation
from database.models.agent_step import AgentStep
from database.models.tool_call import ToolCall


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()