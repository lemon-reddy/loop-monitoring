import os

from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

DATABASE_URL = os.environ.get("DATABASE_URL")
