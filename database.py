"""PostgreSQL connection setup.

Reads DB connection settings from environment variables (via `.env`):
  - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
"""

from peewee import PostgresqlDatabase
from dotenv import load_dotenv
import os

load_dotenv()

print("DB Name:", os.getenv("DB_NAME"))
print("DB User:", os.getenv("DB_USER"))
print("DB Host:", os.getenv("DB_HOST"))
print("DB Port:", os.getenv("DB_PORT"))

db = PostgresqlDatabase(
    os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
)