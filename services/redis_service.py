import os
import logging

import redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_ENABLED

logger = logging.getLogger(__name__)


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
