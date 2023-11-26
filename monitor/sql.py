from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .env import DATABASE_URL

engine = create_engine(url=DATABASE_URL)

session = scoped_session(sessionmaker(engine))
