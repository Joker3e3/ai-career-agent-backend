import os
import logging

import redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

logger = logging.getLogger(__name__)

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


redis_client = None

if REDIS_ENABLED:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=0.2,
        socket_timeout=0.2,
        retry=Retry(NoBackoff(), 0),
        health_check_interval=30,
    )


def is_redis_available() -> bool:
    if redis_client is None:
        return False

    try:
        return bool(redis_client.ping())
    except RedisError as exc:
        logger.warning("Redis unavailable at %s:%s: %s", REDIS_HOST, REDIS_PORT, exc)
        return False
