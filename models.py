"""Database models (Peewee ORM) for DAAGS.

Includes:
  - Employees/customers/products/orders/items (for the "retail" schema)
  - Transaction table used by `daags_engine` to store generated purchases
"""

from peewee import *
from database import db
from datetime import datetime

class BaseModel(Model):
    class Meta:
        database = db

class Employee(BaseModel):
    first_name = CharField()
    last_name = CharField()

class Customer(BaseModel):
    name = CharField()
    email = CharField(unique=True)

class Product(BaseModel):
    name = CharField()
    price = FloatField()

class Order(BaseModel):
    customer = ForeignKeyField(Customer, backref="orders")
    created_at = DateTimeField(default=datetime.now)

class OrderItem(BaseModel):
    order = ForeignKeyField(Order, backref="items")
    product = ForeignKeyField(Product)
    quantity = IntegerField()
    price_at_sale = FloatField()


# Generated retail transactions (DAAGS output)
# product_id stores the product's unique identifier (e.g. ASIN from amazon_products.csv)
class Transaction(BaseModel):
    transaction_id = BigIntegerField(primary_key=True)
    user_id = IntegerField(index=True)
    state = CharField(max_length=2, index=True)
    item_count = IntegerField()
    product_id = CharField(max_length=64, index=True)
    amount = DecimalField(max_digits=10, decimal_places=2)
    payment_method = CharField(max_length=20, index=True)
    timestamp = DateTimeField(index=True)

    class Meta:
        table_name = "transactions"
