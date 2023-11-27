from .session import redis_session


def check_exists(redis_key):
    return redis_session.exists(redis_key)
