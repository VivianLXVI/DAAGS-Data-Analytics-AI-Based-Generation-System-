"""One-off schema creation script.

Creates tables defined in `models.py` if they don't already exist.
"""

from database import db
from models import *

def create_tables():
    with db:
        db.create_tables([
            Employee,
            Customer,
            Product,
            Order,
            OrderItem
        ])

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")
