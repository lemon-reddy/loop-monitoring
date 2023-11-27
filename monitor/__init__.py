from fastapi import FastAPI
from . import main

app = FastAPI()
app.include_router(main.router)
