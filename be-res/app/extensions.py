from logging.handlers import RotatingFileHandler
from flask import logging
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

cache = Cache(config={
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_HOST": "redis",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_DEFAULT_TIMEOUT": 300
})
limiter = Limiter(key_func=get_remote_address)

