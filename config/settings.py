from dotenv import load_dotenv
import os

load_dotenv()

WORKFLOW_STATE_TTL = int(
    os.getenv("WORKFLOW_STATE_TTL", 86400)
)

CONFIRMATION_TTL = int(
    os.getenv("CONFIRMATION_TTL", 86400)
)

SESSION_MEMORY_TTL = int(
    os.getenv("SESSION_MEMORY_TTL", 2592000)
)