from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
import redis

from .env import DATABASE_URL, REDIS_URL

engine = create_engine(url=DATABASE_URL)

db_session = scoped_session(sessionmaker(engine))
redis_session = redis.Redis.from_url(REDIS_URL, decode_responses=True)
