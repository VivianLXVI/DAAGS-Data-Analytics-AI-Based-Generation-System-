"""Legacy order generator.

This script generates `Order` and `OrderItem` rows using the relational
schema in `models.py`. It is separate from the DAAGS transaction generator
(`python -m daags_engine.run`).
"""

import random
from models import Customer, Product, Order, OrderItem
from database import db

def generate_order():
    customers = list(Customer.select())
    products = list(Product.select())

    customer = random.choice(customers)
    order = Order.create(customer=customer)

    num_items = random.randint(1, 3)
    selected_products = random.sample(products, num_items)

    for product in selected_products:
        OrderItem.create(
            order=order,
            product=product,
            quantity=random.randint(1, 5),
            price_at_sale=product.price
        )

    print(f"Generated order {order.id}")

if __name__ == "__main__":
    with db:
        generate_order()
