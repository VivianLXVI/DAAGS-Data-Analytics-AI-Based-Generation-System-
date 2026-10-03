"""
Product catalog: product_id → name, price, and category.

Products and categories are loaded from a CSV file whose path is configured
in daags_engine.config.PRODUCTS_CSV_PATH.

Expected CSV format (header row required):
    product_id,name,price,category

- product_id: integer
- name: string
- price: float
- category: string (must match the category names used in state_config
  category_weights, e.g. gaming, tech, books, etc.)
"""

import csv
import os
from glob import glob
from collections import defaultdict

from daags_engine.config import PRODUCTS_CSV_PATH

# To keep startup fast with very large source files (e.g. 1M+ Amazon rows),
# cap how many products we actually load into the in-memory catalog.
MAX_PRODUCTS_PER_CATEGORY = 2_000
MAX_TOTAL_PRODUCTS = 50_000

# product_id (e.g. ASIN) -> { "name": str, "price": float, "category": str }
PRODUCT_CATALOG = {}

# category -> [product_id, ...]
CATEGORY_PRODUCTS = defaultdict(list)

# product_id -> category
PRODUCT_CATEGORY = {}


def _load_products_from_csv() -> None:
    try:
        # Resolve path: allow either a direct CSV file or a directory containing a CSV.
        csv_path = PRODUCTS_CSV_PATH
        if os.path.isdir(csv_path):
            matches = sorted(glob(os.path.join(csv_path, "*.csv")))
            if not matches:
                raise FileNotFoundError(
                    f"No CSV files found in directory '{csv_path}'. "
                    f"Place a products CSV there or point PRODUCTS_CSV_PATH to a file."
                )
            csv_path = matches[0]

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            lower_map = {name.lower(): name for name in fieldnames}

            def has_cols(*cols: str) -> bool:
                return all(c in lower_map for c in cols)

            total_loaded = 0
            per_category_count = defaultdict(int)

            def can_add(category: str) -> bool:
                if total_loaded >= MAX_TOTAL_PRODUCTS:
                    return False
                if per_category_count[category] >= MAX_PRODUCTS_PER_CATEGORY:
                    return False
                return True

            # Case 1: generic products.csv with explicit product_id,name,price,category
            if has_cols("product_id", "name", "price", "category"):
                pid_col = lower_map["product_id"]
                name_col = lower_map["name"]
                price_col = lower_map["price"]
                category_col = lower_map["category"]

                for row in reader:
                    if total_loaded >= MAX_TOTAL_PRODUCTS:
                        break

                    pid = str(row[pid_col])
                    name = row[name_col]
                    try:
                        price = float(row[price_col])
                    except (TypeError, ValueError):
                        continue
                    category = row[category_col]

                    if not can_add(category):
                        continue

                    PRODUCT_CATALOG[pid] = {
                        "name": name,
                        "price": price,
                        "category": category,
                    }
                    CATEGORY_PRODUCTS[category].append(pid)
                    PRODUCT_CATEGORY[pid] = category
                    per_category_count[category] += 1
                    total_loaded += 1

            # Case 2: amazon_products.csv style (asin + other columns)
            elif "asin" in lower_map:
                pid_col = lower_map["asin"]
                # Try a few common name/title columns
                name_col = (
                    lower_map.get("title")
                    or lower_map.get("product_title")
                    or lower_map.get("item_name")
                    or lower_map.get("name")
                    or pid_col
                )
                # Category-ish columns
                category_col = (
                    lower_map.get("main_cat")
                    or lower_map.get("category")
                    or lower_map.get("categories")
                )
                # Price-like columns (may be missing or non-numeric)
                price_col = (
                    lower_map.get("price")
                    or lower_map.get("list_price")
                    or lower_map.get("price_usd")
                )

                for row in reader:
                    if total_loaded >= MAX_TOTAL_PRODUCTS:
                        break

                    pid = row[pid_col]
                    if not pid:
                        continue

                    name = row.get(name_col, pid)

                    price = 0.0
                    if price_col and row.get(price_col):
                        try:
                            price = float(row[price_col])
                        except (TypeError, ValueError):
                            price = 0.0

                    raw_category = row.get(category_col, "") if category_col else ""
                    # Map the raw Amazon category into one of the behavior categories
                    category = _map_source_category_to_behavior_category(raw_category)

                    if not can_add(category):
                        continue

                    PRODUCT_CATALOG[pid] = {
                        "name": name,
                        "price": price,
                        "category": category,
                    }
                    CATEGORY_PRODUCTS[category].append(pid)
                    PRODUCT_CATEGORY[pid] = category
                    per_category_count[category] += 1
                    total_loaded += 1

            else:
                raise ValueError(
                    "Unsupported products CSV format. Expected either "
                    "product_id,name,price,category columns or an 'asin' column."
                )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Products CSV not found at '{PRODUCTS_CSV_PATH}'. "
            f"Please create it with either columns: product_id,name,price,category "
            f"or an amazon_products.csv-style file containing an 'asin' column."
        ) from exc


def _map_source_category_to_behavior_category(raw_category: str) -> str:
    """
    Map an arbitrary source category (e.g. from amazon_products.csv) into one of the
    behavior categories used by state_config (gaming, tech, books, fitness, etc.).
    """
    text = (raw_category or "").lower()

    if any(k in text for k in ["video game", "xbox", "playstation", "nintendo", "gaming"]):
        return "gaming"
    if any(k in text for k in ["book", "novel", "textbook", "magazine", "comic"]):
        return "books"
    if any(k in text for k in ["laptop", "computer", "pc", "electronics", "phone", "tablet"]):
        return "tech"
    if any(k in text for k in ["fitness", "exercise", "sport", "outdoor", "gym", "running"]):
        return "fitness"
    if any(k in text for k in ["kitchen", "cook", "cookware", "appliance", "bake"]):
        return "kitchen"
    if any(k in text for k in ["camera", "photo", "photography", "dslr"]):
        return "photo"
    if any(k in text for k in ["music", "instrument", "guitar", "piano"]):
        return "music"
    if any(k in text for k in ["garden", "outdoor decor", "patio", "lawn"]):
        return "garden"
    if any(k in text for k in ["luggage", "travel", "suitcase"]):
        return "travel"
    if any(k in text for k in ["clothing", "shoe", "apparel", "dress", "fashion"]):
        return "fashion"
    if any(k in text for k in ["beauty", "cosmetic", "makeup", "skincare"]):
        return "beauty"
    if any(k in text for k in ["pet", "dog", "cat", "animal"]):
        return "pets"
    if any(k in text for k in ["tool", "hardware", "diy", "home improvement"]):
        return "diy"
    if any(k in text for k in ["fan gear", "team", "jersey", "sports"]):
        return "sports"
    if any(k in text for k in ["gourmet", "food", "snack", "coffee", "tea", "kitchen staple"]):
        return "gourmet"

    # Default catch-all
    return "tech"


# Load products at import time so generator/state_config can use them immediately.
_load_products_from_csv()


def get_products_for_category(category: str) -> list:
    """Return list of product_ids for the given product category."""
    return CATEGORY_PRODUCTS[category].copy()


def get_product_category(product_id: int) -> str:
    """Return category name for product_id."""
    return PRODUCT_CATEGORY[product_id]


def get_product_price(product_id: int) -> float:
    """Return catalog price for product_id."""
    return PRODUCT_CATALOG[product_id]["price"]


def get_product_name(product_id: int) -> str:
    """Return catalog name for product_id."""
    return PRODUCT_CATALOG[product_id]["name"]
