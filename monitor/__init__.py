from fastapi import FastAPI, Depends
from . import main
from .session import db_session
from sqlalchemy.exc import SQLAlchemyError


async def close_session():
    yield
    try:
        db_session.commit()
    except SQLAlchemyError:
        db_session.rollback()
    db_session.close()


app = FastAPI()
app.include_router(main.router, dependencies=[Depends(close_session)])
