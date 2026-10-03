"""daags_engine configuration.

This file contains the knobs that control:
  - how many transactions to generate
  - the time range
  - where CSV output is written
  - which US states are included in a run (each row gets one state from this set)
  - where to load products from
"""

import os

# Target generation size
TOTAL_RECORDS = 500   # change for testing (ex: 100_000)

# Time range
START_YEAR = 2023
END_YEAR = 2024

# Output settings
OUTPUT_FOLDER = "daags_engine/outputs/"
OUTPUT_FILE = "transactions.csv"

# Output destination: "csv" | "postgres" | "both"
OUTPUT_MODE = "both"

# Optional: path to a products CSV *file or directory*.
# - If this points to a file, that CSV is used.
# - If this points to a directory, the first *.csv found in that directory is used.
# Expected CSV columns (header row is required):
#   product_id,name,price,category
PRODUCTS_CSV_PATH = "daags_engine/inputs"

# Per-state population and census region for sampling / behavior (see state_config).
# Expected CSV columns: state,population,region
STATE_DATA_CSV_PATH = "daags_engine/inputs/state_data.csv"

# US states included in this simulation run (e.g. ("CA",) or ("CA", "TX", "NY")).
# Each transaction is assigned one state from this set, sampled with weights
# proportional to census population × per-state purchase_freq_factor (see state_config.sample_state_from_subset).
# Codes are case-insensitive; unknown codes are ignored. Must resolve to at least one valid state.
ACTIVE_STATES = (
    "CA",
    "TX",
    "NY",
    "FL",
    "IL",
    "OH",
    "MI",
    "IN",
    "IA",
    "KS",
    "MO",
    "NE",
    "ND",
    "SD",
    "WI",
    "MN",
)

# Batch size for streaming writes
BATCH_SIZE = 10

# -----------------------------
# Optional: OpenRouter weight tuning
# -----------------------------
# If enabled, `daags_engine.state_config` can call OpenRouter to adjust the
# state/category weights used during dataset generation.
#
# Recommended:
# - set `OPENROUTER_WEIGHT_TUNING_ENABLED=true` only when you want the AI call
# - leave it disabled for normal fast runs
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
OPENROUTER_WEIGHT_TUNING_ENABLED = os.getenv("OPENROUTER_WEIGHT_TUNING_ENABLED", "false").lower() == "true"
OPENROUTER_WEIGHT_TUNING_ALWAYS_REFRESH = os.getenv("OPENROUTER_WEIGHT_TUNING_ALWAYS_REFRESH", "false").lower() == "true"

# Path where OpenRouter-tuned overrides are cached.
OPENROUTER_STATE_CONFIG_OVERRIDE_PATH = os.getenv(
    "OPENROUTER_STATE_CONFIG_OVERRIDE_PATH",
    "daags_engine/outputs/state_config/state_config_override.json",
)

# =============================================================================
# UNIVERSAL CSV INPUT MODE
# =============================================================================
# Set UNIVERSAL_CSV_MODE=true to use the universal CSV input generator
# instead of the default DAAGS transaction generator.
#
# When enabled:
# - UNIVERSAL_CSV_INPUT_PATH specifies the input CSV file
# - TOTAL_RECORDS still controls number of rows to generate
# - The system analyzes the CSV and generates synthetic data maintaining patterns
UNIVERSAL_CSV_MODE = os.getenv("UNIVERSAL_CSV_MODE", "false").lower() == "true"
UNIVERSAL_CSV_INPUT_PATH = os.getenv("UNIVERSAL_CSV_INPUT_PATH", "")
UNIVERSAL_CSV_OUTPUT_FILE = os.getenv("UNIVERSAL_CSV_OUTPUT_FILE", "daags_engine/outputs/synthetic_data.csv")
