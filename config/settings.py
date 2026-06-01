import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
import os

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

WORKFLOW_STATE_TTL = int(os.getenv("WORKFLOW_STATE_TTL", 86400))

CONFIRMATION_TTL = int(os.getenv("CONFIRMATION_TTL", 86400))

SESSION_MEMORY_TTL = int(os.getenv("SESSION_MEMORY_TTL", 2592000))

REDIS_CONFIGURED_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() not in {
    "0",
    "false",
    "no",
    "off",
}
RUNNING_IN_DOCKER = os.path.exists("/.dockerenv")


def _resolve_redis_host() -> str:
    if (
        not RUNNING_IN_DOCKER
        and REDIS_CONFIGURED_HOST not in {"localhost", "127.0.0.1", "::1"}
        and "." not in REDIS_CONFIGURED_HOST
    ):
        logger.warning(
            "REDIS_HOST=%s looks like a Docker service name, but this app is "
            "running on the host. Falling back to 127.0.0.1.",
            REDIS_CONFIGURED_HOST,
        )
        return "127.0.0.1"

    return REDIS_CONFIGURED_HOST


REDIS_HOST = _resolve_redis_host()
