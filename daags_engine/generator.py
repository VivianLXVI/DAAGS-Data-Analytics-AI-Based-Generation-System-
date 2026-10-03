"""
DAAGS transaction generator.

This module generates synthetic "transactions" (one row per purchase) and can
write them to:
  - CSV (streaming appends)
  - PostgreSQL (batched inserts)

Behavior is driven by:
  - `ACTIVE_STATES` from `daags_engine.config` (each transaction draws one state from this set)
  - state category weights from `daags_engine.state_config`
  - a products catalog loaded from CSV in `daags_engine.product_catalog`

Each transaction represents a variable-size cart:
  - 1 to 10 items
  - `item_count` and cart total `amount` are computed from chosen products
"""

import random
import os
from datetime import datetime, timedelta

from daags_engine.config import (
    TOTAL_RECORDS,
    START_YEAR,
    END_YEAR,
    OUTPUT_FOLDER,
    OUTPUT_FILE,
    BATCH_SIZE,
    OUTPUT_MODE,
    ACTIVE_STATES,
)

from daags_engine.product_catalog import (
    get_products_for_category,
    get_product_price,
)

from daags_engine.state_config import (
    get_state_behavior,
    sample_state_from_subset,
)

from daags_engine.io_files.csv_writer import (
    ensure_output_folder,
    write_batch as write_csv_batch,
)

from daags_engine.io_files.postgres_writer import (
    ensure_table,
    write_batch as write_postgres_batch,
)

# User IDs 1..NUM_USERS; users are assigned to states dynamically per-transaction.
NUM_USERS = 10_000


def random_date():
    start = datetime(START_YEAR, 1, 1)
    end = datetime(END_YEAR, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59), seconds=random.randint(0, 59))


def generate_transaction(transaction_id: int):
    """
    Generate a single transaction with a variable-size cart (1–10 items).

    - State is drawn from ACTIVE_STATES (population-weighted within that set).
    - Cart size and category mix are driven by that state's behavior.
    - The dataset stores:
        - total amount spent for the cart
        - item_count (number of products in the cart)
        - a representative product_id from the cart (first item)
    """
    user_id = random.randint(1, NUM_USERS)

    state = sample_state_from_subset(ACTIVE_STATES)
    behavior = get_state_behavior(state)

    # Pick timestamp first so we can apply winter/summer-style seasonality.
    timestamp = random_date()
    month = timestamp.month

    min_items = max(1, behavior.min_items)
    max_items = min(10, behavior.max_items)
    if max_items < min_items:
        max_items = min_items

    item_count = random.randint(min_items, max_items)
    month_multiplier = behavior.month_item_multiplier.get(str(month), 1.0)
    item_count = int(round(item_count * float(month_multiplier)))
    item_count = max(1, min(10, item_count))

    # Only keep categories that actually have products in the catalog.
    available_categories = []
    available_weights = []
    for cat, w in behavior.category_weights.items():
        products = get_products_for_category(cat)
        if products:
            available_categories.append(cat)
            available_weights.append(w)

    if not available_categories:
        raise RuntimeError("No products available for any category in the current state behavior.")

    categories = available_categories
    weights = available_weights

    total_amount = 0.0
    representative_product_id = None
    price_spread = getattr(behavior, "price_spread", 0.05)

    for i in range(item_count):
        category = random.choices(categories, weights=weights, k=1)[0]
        product_ids = get_products_for_category(category)
        product_id = random.choice(product_ids)
        price = get_product_price(product_id)
        # Apply state-driven price variance so totals aren't perfectly deterministic.
        if price_spread and price > 0:
            price = round(price * random.uniform(1 - price_spread, 1 + price_spread), 2)
        total_amount += price
        if representative_product_id is None:
            representative_product_id = product_id

    total_amount = round(total_amount, 2)

    payment_weights = getattr(behavior, "payment_method_weights", None) or {
        "card": 1.0,
        "cash": 1.0,
        "online": 1.0,
    }
    payment_method = random.choices(
        list(payment_weights.keys()),
        weights=list(payment_weights.values()),
        k=1,
    )[0]

    return [
        transaction_id,
        user_id,
        state,
        item_count,
        representative_product_id,
        total_amount,
        payment_method,
        timestamp.isoformat(),
    ]


def run_generation():
    # Resolve and validate ACTIVE_STATES once (fail fast with a clear error).
    sample_state_from_subset(ACTIVE_STATES)

    write_csv = OUTPUT_MODE in ("csv", "both")
    write_postgres = OUTPUT_MODE in ("postgres", "both")

    if write_csv:
        ensure_output_folder(OUTPUT_FOLDER)
        file_path = OUTPUT_FOLDER + OUTPUT_FILE
        # On Windows, the CSV might be locked by Excel/another viewer.
        # Try to remove the old file; if we can't, write to a new timestamped file.
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except PermissionError:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = OUTPUT_FOLDER + f"transactions_{run_id}.csv"
            print(f"CSV file was locked; writing to: {file_path}")

    if write_postgres:
        ensure_table()

    header = [
        "transaction_id",
        "user_id",
        "state",
        "item_count",
        "product_id",
        "amount",
        "payment_method",
        "timestamp",
    ]

    total_batches = TOTAL_RECORDS // BATCH_SIZE
    remaining_batch = TOTAL_RECORDS % BATCH_SIZE
    dest = ", ".join(filter(None, ["CSV" if write_csv else None, "PostgreSQL" if write_postgres else None]))

    print(f"Generating {TOTAL_RECORDS} records in {total_batches} batches" + (f" + 1 remainder ({remaining_batch} rows)" if remaining_batch else "") + f" → {dest}")

    for batch in range(total_batches):
        rows = []

        start_id = batch * BATCH_SIZE

        for i in range(BATCH_SIZE):
            transaction_id = start_id + i + 1
            rows.append(generate_transaction(transaction_id))

        if write_csv:
            write_csv_batch(
                file_path=file_path,
                rows=rows,
                header=header,
                write_header=(batch == 0),
            )

        if write_postgres:
            write_postgres_batch(rows=rows)

        print(f"Batch {batch + 1}/{total_batches} written")

    if remaining_batch != 0:
        rows = []
        start_id = total_batches * BATCH_SIZE

        for i in range(remaining_batch):
            transaction_id = start_id + i + 1
            rows.append(generate_transaction(transaction_id))

        if write_csv:
            write_csv_batch(
                file_path=file_path,
                rows=rows,
                header=header,
                write_header=False,
            )

        if write_postgres:
            write_postgres_batch(rows=rows)

        print(f"Remainder batch ({remaining_batch} rows) written")

    print("Generation complete.")
