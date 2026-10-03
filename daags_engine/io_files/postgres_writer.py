"""
PostgreSQL bulk writer for DAAGS-generated transactions.
Uses batched inserts for high throughput with 5M+ records.
"""

import sys
from pathlib import Path

# Ensure project root is on path for database/models imports
_project_root = Path(__file__).resolve().parents[1] # Hardcoded relative path, changed from [2] to [1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from models import Transaction
from database import db


# Rows per INSERT statement (keeps query size manageable; PostgreSQL handles 10k+ fine)
INSERT_CHUNK_SIZE = 10_000


def ensure_table():
    """Create transactions table if it does not exist; migrate columns if needed.

    On every run:
    - Ensures columns product_id, state, and item_count exist (for older DBs).
    - Ensures product_id is text-capable (to hold ASIN strings).
    - Truncates the table so each run starts with a fresh dataset.
    """
    db.connect()
    try:
        # Migration: if transactions table exists but lacks newer columns, add them
        cursor = db.execute_sql(
            """
            SELECT 1 FROM information_schema.tables WHERE table_name = 'transactions';
            """
        )
        if cursor.fetchone():
            # Helper to add a column if missing
            def _ensure_column(column_name: str, column_type_sql: str, index_sql: str | None = None):
                col_cursor = db.execute_sql(
                    f"""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'transactions' AND column_name = '{column_name}';
                    """
                )
                if col_cursor.fetchone() is None:
                    db.execute_sql(f"ALTER TABLE transactions ADD COLUMN {column_name} {column_type_sql};")
                    if index_sql:
                        db.execute_sql(index_sql)

            _ensure_column("product_id", "VARCHAR(64)", "CREATE INDEX IF NOT EXISTS transactions_product_id ON transactions (product_id);")
            _ensure_column("state", "CHAR(2)", "CREATE INDEX IF NOT EXISTS transactions_state ON transactions (state);")
            _ensure_column("item_count", "INTEGER", None)

            # Make sure product_id can hold string identifiers (e.g. ASIN)
            try:
                db.execute_sql("ALTER TABLE transactions ALTER COLUMN product_id TYPE VARCHAR(64);")
            except Exception:
                # If the type is already compatible, this will fail harmlessly.
                pass

        db.create_tables([Transaction], safe=True)
        # Clear old data so each run creates a fresh dataset
        db.execute_sql("TRUNCATE TABLE transactions RESTART IDENTITY;")
    finally:
        db.close()


def write_batch(rows: list, header: list = None):
    """
    Bulk-insert a batch of rows into PostgreSQL.
    rows: list of [transaction_id, user_id, state, item_count, product_id, amount, payment_method, timestamp]
    """
    if not rows:
        return

    # Convert generator rows to dicts for Peewee insert_many
    data = [
        {
            "transaction_id": r[0],
            "user_id": r[1],
            "state": r[2],
            "item_count": r[3],
            "product_id": r[4],
            "amount": str(r[5]),  # Peewee DecimalField accepts string
            "payment_method": r[6],
            "timestamp": r[7],
        }
        for r in rows
    ]

    db.connect()
    try:
        for i in range(0, len(data), INSERT_CHUNK_SIZE):
            chunk = data[i : i + INSERT_CHUNK_SIZE]
            Transaction.insert_many(chunk).execute()
    finally:
        db.close()
