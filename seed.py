"""Seeding helpers for the relational tables in `models.py`.

This script uses `faker` to create example `Employee`, `Customer`, and
`Product` rows (separate from the DAAGS transaction generator).
"""

from faker import Faker
from models import Employee, Customer, Product
from database import db
import random

fake = Faker()

def seed_employees(n=5):
    for _ in range(n):
        Employee.create(
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )

def seed_customers(n=10):
    for _ in range(n):
        Customer.create(
            name=fake.name(),
            email=fake.unique.email()
        )

def seed_products(n=8):
    for _ in range(n):
        Product.create(
            name=fake.word().capitalize(),
            price=round(random.uniform(5, 200), 2)
        )

if __name__ == "__main__":
    with db:
        seed_products()
    print("Products seeded.")
