"""
US state configuration for DAAGS simulations.

This file defines the per-state "behavior" parameters that drive:
- cart size (min/max items)
- category preferences (category_weights)
- payment method choice (payment_method_weights)
- price spread/variance (price_spread)

Optionally, if OpenRouter weight tuning is enabled, the base per-state
parameters can be adjusted using an LLM and cached to disk.
"""

from dataclasses import dataclass
from typing import Dict, Any, Iterable, List, Tuple
import csv
import random
import json
import os
import hashlib
from pathlib import Path

from daags_engine.config import (
    OPENROUTER_WEIGHT_TUNING_ENABLED,
    OPENROUTER_WEIGHT_TUNING_ALWAYS_REFRESH,
    OPENROUTER_STATE_CONFIG_OVERRIDE_PATH,
    STATE_DATA_CSV_PATH,
    ACTIVE_STATES,
)
from daags_engine.openrouter_weight_tuner import request_state_weight_overrides


def _load_state_data_csv(path: str) -> Tuple[Dict[str, int], Dict[str, str]]:
    """Load population and region per state from CSV (columns: state, population, region)."""
    population: Dict[str, int] = {}
    region_map: Dict[str, str] = {}
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(
            f"State data CSV not found: {path}. Expected columns: state, population, region."
        )
    with p.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"State data CSV has no header row: {path}")
        for row in reader:
            code = (row.get("state") or "").strip().upper()
            if not code:
                continue
            raw_pop = row.get("population")
            if raw_pop is None or str(raw_pop).strip() == "":
                continue
            pop = int(str(raw_pop).strip().replace(",", ""))
            reg = (row.get("region") or "Midwest").strip()
            population[code] = pop
            region_map[code] = reg
    if not population:
        raise ValueError(f"No state rows loaded from {path}")
    return population, region_map


STATE_POPULATION, STATE_REGION = _load_state_data_csv(STATE_DATA_CSV_PATH)


@dataclass(frozen=True)
class StateBehavior:
    purchase_freq_factor: float
    min_items: int
    max_items: int
    category_weights: Dict[str, float]
    payment_method_weights: Dict[str, float]
    # Symmetric spread applied to catalog price when computing cart totals.
    # Example: price_spread=0.05 makes each item price vary by +/- 5%.
    price_spread: float
    # Month-level multiplier applied to the cart size (item_count) after min/max are sampled.
    # Keys are strings "1".."12" so the structure can be encoded/decoded from JSON easily.
    month_item_multiplier: Dict[str, float]


# Default: no seasonality adjustment (AI can override these values).
DEFAULT_MONTH_ITEM_MULTIPLIER: Dict[str, float] = {str(m): 1.0 for m in range(1, 13)}


# Region-level defaults; all category keys map to product_catalog categories.
REGION_BEHAVIOR: Dict[str, StateBehavior] = {
    "Northeast": StateBehavior(
        purchase_freq_factor=1.05,
        min_items=1,
        max_items=6,
        category_weights={
            "tech": 1.4,
            "books": 1.6,
            "gourmet": 1.4,
            "travel": 1.1,
            "sports": 0.9,
            "gaming": 1.0,
            "fitness": 1.0,
            "kitchen": 1.1,
            "photo": 1.0,
            "music": 1.0,
            "garden": 0.8,
            "fashion": 1.3,
            "beauty": 1.2,
            "pets": 1.0,
            "diy": 0.9,
        },
        payment_method_weights={"card": 0.45, "cash": 0.15, "online": 0.40},
        price_spread=0.05,
        month_item_multiplier=DEFAULT_MONTH_ITEM_MULTIPLIER,
    ),
    "Midwest": StateBehavior(
        purchase_freq_factor=0.95,
        min_items=1,
        max_items=7,
        category_weights={
            "tech": 1.0,
            "books": 1.1,
            "gourmet": 0.9,
            "travel": 0.9,
            "sports": 1.3,
            "gaming": 1.1,
            "fitness": 1.1,
            "kitchen": 1.2,
            "photo": 0.9,
            "music": 1.0,
            "garden": 1.3,
            "fashion": 0.9,
            "beauty": 1.0,
            "pets": 1.2,
            "diy": 1.3,
        },
        payment_method_weights={"card": 0.43, "cash": 0.25, "online": 0.32},
        price_spread=0.055,
        month_item_multiplier=DEFAULT_MONTH_ITEM_MULTIPLIER,
    ),
    "South": StateBehavior(
        purchase_freq_factor=1.10,
        min_items=2,
        max_items=8,
        category_weights={
            "tech": 1.0,
            "books": 0.9,
            "gourmet": 1.1,
            "travel": 1.2,
            "sports": 1.4,
            "gaming": 1.3,
            "fitness": 1.2,
            "kitchen": 1.1,
            "photo": 1.0,
            "music": 1.3,
            "garden": 1.1,
            "fashion": 1.1,
            "beauty": 1.2,
            "pets": 1.3,
            "diy": 1.1,
        },
        payment_method_weights={"card": 0.42, "cash": 0.32, "online": 0.26},
        price_spread=0.06,
        month_item_multiplier=DEFAULT_MONTH_ITEM_MULTIPLIER,
    ),
    "West": StateBehavior(
        purchase_freq_factor=1.15,
        min_items=1,
        max_items=10,
        category_weights={
            "tech": 1.6,
            "books": 1.1,
            "gourmet": 1.4,
            "travel": 1.5,
            "sports": 1.0,
            "gaming": 1.2,
            "fitness": 1.4,
            "kitchen": 1.0,
            "photo": 1.2,
            "music": 1.1,
            "garden": 1.0,
            "fashion": 1.3,
            "beauty": 1.3,
            "pets": 1.1,
            "diy": 0.9,
        },
        payment_method_weights={"card": 0.35, "cash": 0.18, "online": 0.47},
        price_spread=0.05,
        month_item_multiplier=DEFAULT_MONTH_ITEM_MULTIPLIER,
    ),
}


def _build_state_behavior() -> Dict[str, StateBehavior]:
    behaviors: Dict[str, StateBehavior] = {}
    for state in STATE_POPULATION:
        region = STATE_REGION.get(state, "Midwest")
        base = REGION_BEHAVIOR.get(region, REGION_BEHAVIOR["Midwest"])

        # Provide per-state variation so the AI has more independent knobs.
        # Deterministic by state code.
        rng = random.Random(state)

        def clamp_int(v: int, lo: int, hi: int) -> int:
            return max(lo, min(hi, v))

        purchase_freq_factor = base.purchase_freq_factor * rng.uniform(0.85, 1.15)

        min_items = clamp_int(int(round(base.min_items * rng.uniform(0.9, 1.1))), 1, 10)
        max_items = clamp_int(int(round(base.max_items * rng.uniform(0.9, 1.1))), 1, 10)
        if max_items < min_items:
            max_items = min_items

        category_weights = {
            k: max(0.01, v * rng.uniform(0.85, 1.15)) for k, v in base.category_weights.items()
        }

        payment_method_weights = {
            k: max(0.01, v * rng.uniform(0.85, 1.15)) for k, v in base.payment_method_weights.items()
        }

        price_spread = max(0.0, min(0.2, base.price_spread * rng.uniform(0.85, 1.15)))

        # Apply small deterministic month variation by state to avoid perfectly-flat carts.
        month_item_multiplier = {
            str(m): max(0.2, min(2.0, float(base.month_item_multiplier[str(m)]) * rng.uniform(0.9, 1.1)))
            for m in range(1, 13)
        }

        behaviors[state] = StateBehavior(
            purchase_freq_factor=purchase_freq_factor,
            min_items=min_items,
            max_items=max_items,
            category_weights=category_weights,
            payment_method_weights=payment_method_weights,
            price_spread=price_spread,
            month_item_multiplier=month_item_multiplier,
        )
    return behaviors


STATE_BEHAVIOR: Dict[str, StateBehavior] = _build_state_behavior()

def _apply_overrides(overrides: Dict[str, Any]) -> None:
    """
    Apply OpenRouter overrides in-place to STATE_BEHAVIOR.
    Expects overrides in the format: { "overrides": { "CA": { ... }, ... } }
    """
    root = overrides or {}
    override_map = root.get("overrides", root)
    if not isinstance(override_map, dict):
        return

    for state_code, tuned in override_map.items():
        if state_code not in STATE_BEHAVIOR or not isinstance(tuned, dict):
            continue

        current = STATE_BEHAVIOR[state_code]

        purchase_freq_factor = float(tuned.get("purchase_freq_factor", current.purchase_freq_factor))
        min_items = int(tuned.get("min_items", current.min_items))
        max_items = int(tuned.get("max_items", current.max_items))
        if min_items < 1:
            min_items = 1
        if max_items < min_items:
            max_items = min_items
        if max_items > 10:
            max_items = 10

        category_weights = current.category_weights.copy()
        tw = tuned.get("category_weights", {})
        if isinstance(tw, dict):
            for k, v in tw.items():
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if fv < 0:
                    continue
                category_weights[k] = max(0.01, fv)

        payment_method_weights = current.payment_method_weights.copy()
        pmw = tuned.get("payment_method_weights", {})
        if isinstance(pmw, dict):
            for k, v in pmw.items():
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if fv < 0:
                    continue
                payment_method_weights[k] = max(0.01, fv)

        price_spread = float(tuned.get("price_spread", current.price_spread))
        if price_spread < 0:
            price_spread = 0.0
        if price_spread > 0.2:
            price_spread = 0.2

        month_item_multiplier = current.month_item_multiplier.copy()
        mium = tuned.get("month_item_multiplier", {})
        if isinstance(mium, dict):
            for mk, mv in mium.items():
                mkey = str(mk)
                try:
                    fmv = float(mv)
                except (TypeError, ValueError):
                    continue
                if fmv < 0.2:
                    fmv = 0.2
                if fmv > 2.0:
                    fmv = 2.0
                month_item_multiplier[mkey] = fmv

        STATE_BEHAVIOR[state_code] = StateBehavior(
            purchase_freq_factor=purchase_freq_factor,
            min_items=min_items,
            max_items=max_items,
            category_weights=category_weights,
            payment_method_weights=payment_method_weights,
            price_spread=price_spread,
            month_item_multiplier=month_item_multiplier,
        )


def _instruction_cache_path(instruction: str) -> str:
    """
    Create a stable cache path per unique instruction.

    `OPENROUTER_STATE_CONFIG_OVERRIDE_PATH` is used as a base; if it's a file,
    we append `_hash` before `.json` (or just append if no extension).
    """
    base = OPENROUTER_STATE_CONFIG_OVERRIDE_PATH
    base_path = Path(base)
    ins_hash = hashlib.sha256((instruction or "").strip().encode("utf-8")).hexdigest()[:12]

    if base_path.suffix.lower() == ".json":
        return str(base_path.with_name(f"{base_path.stem}_{ins_hash}.json"))
    # If it isn't a json file, store a hashed json file next to it.
    return str(base_path.with_name(f"{base_path.name}_{ins_hash}.json"))


def apply_openrouter_tuning(instruction: str) -> None:
    """
    Apply OpenRouter-based tuning for the given instruction.

    Special command:
      - instruction == "default" (case-insensitive) => do not call the AI
    """
    if not OPENROUTER_WEIGHT_TUNING_ENABLED:
        return

    normalized = (instruction or "").strip()
    if not normalized or normalized.lower() == "default":
        return

    override_path = _instruction_cache_path(normalized)
    try:
        if (not OPENROUTER_WEIGHT_TUNING_ALWAYS_REFRESH) and os.path.exists(override_path):
            with open(override_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            _apply_overrides(cached)
            return

        # Build a compact base representation for the LLM.
        base_for_ai: Dict[str, Dict[str, Any]] = {}
        for state_code, behavior in STATE_BEHAVIOR.items():
            base_for_ai[state_code] = {
                "purchase_freq_factor": behavior.purchase_freq_factor,
                "min_items": behavior.min_items,
                "max_items": behavior.max_items,
                "category_weights": behavior.category_weights,
                "payment_method_weights": behavior.payment_method_weights,
                "price_spread": behavior.price_spread,
                "month_item_multiplier": behavior.month_item_multiplier,
            }

        # Restrict tuning to active states when provided to reduce payload size
        # and focus the model on the states that will actually be generated.
        active_state_set = {code.strip().upper() for code in ACTIVE_STATES}
        active_state_list = [
            code for code in STATE_BEHAVIOR.keys() if code.upper() in active_state_set
        ] or list(STATE_BEHAVIOR.keys())

        tuned = request_state_weight_overrides(
            base_for_ai,
            user_instruction=normalized,
            active_states=active_state_list,
        )
        os.makedirs(os.path.dirname(override_path), exist_ok=True)
        with open(override_path, "w", encoding="utf-8") as f:
            json.dump(tuned, f, indent=2)

        _apply_overrides(tuned)
    except Exception:
        # Fail open: if AI tuning fails, generation still works with base weights.
        return


def sample_state() -> str:
    """Sample a state code using population * behavior-adjusted weights."""
    state_codes = list(STATE_POPULATION.keys())
    state_weights = [STATE_POPULATION[s] * STATE_BEHAVIOR[s].purchase_freq_factor for s in state_codes]
    return random.choices(state_codes, weights=state_weights, k=1)[0]


def sample_state_from_subset(state_codes: Iterable[str]) -> str:
    """
    Sample a state from the given codes using population × purchase_freq_factor weights.

    Used when the run is restricted to a subset of states (config ACTIVE_STATES).
    Invalid or empty entries are skipped; duplicates are deduplicated while preserving order.
    """
    seen: set[str] = set()
    normalized: List[str] = []
    for raw in state_codes:
        if raw is None:
            continue
        code = str(raw).strip().upper()
        if not code or code in seen:
            continue
        if code not in STATE_POPULATION:
            continue
        seen.add(code)
        normalized.append(code)

    if not normalized:
        raise ValueError(
            "No valid US state codes in the active set. "
            "Use codes present in STATE_POPULATION (e.g. 'CA', 'TX')."
        )

    if len(normalized) == 1:
        return normalized[0]

    weights = [
        STATE_POPULATION[s] * STATE_BEHAVIOR[s].purchase_freq_factor for s in normalized
    ]
    return random.choices(normalized, weights=weights, k=1)[0]


def get_state_behavior(state_code: str) -> StateBehavior:
    """Return behavior parameters for a given state code (e.g. 'CA')."""
    return STATE_BEHAVIOR[state_code]


#START

def format_state_behavior(
    behavior: StateBehavior,
    *,
    max_category_weights: int = 8,
) -> str:
    """
    Create a compact, human-readable summary of a StateBehavior.

    This is intended for debugging so you can quickly see whether tuning
    changed the key knobs (category weights, payment weights, etc.).
    """
    top_cats = sorted(behavior.category_weights.items(), key=lambda kv: kv[1], reverse=True)
    shown_cats = top_cats[:max_category_weights]
    remaining = max(0, len(top_cats) - len(shown_cats))

    months = behavior.month_item_multiplier
    month_min = min(months.values()) if months else 1.0
    month_max = max(months.values()) if months else 1.0

    payment_str = ", ".join(
        f"{k}={v:.4f}" for k, v in sorted(behavior.payment_method_weights.items())
    )
    cat_str = ", ".join(f"{k}:{v:.4f}" for k, v in shown_cats)
    remaining_str = f" (+{remaining} more)" if remaining else ""

    return (
        f"purchase_freq_factor={behavior.purchase_freq_factor:.4f} "
        f"min_items={behavior.min_items} max_items={behavior.max_items} "
        f"price_spread={behavior.price_spread:.4f} "
        f"month_item_multiplier[min={month_min:.3f}, max={month_max:.3f}] "
        f"top_category_weights=[{cat_str}]{remaining_str} "
        f"payment_method_weights=[{payment_str}]"
    )


def print_state_behavior(
    state_code: str,
    *,
    max_category_weights: int = 8,
) -> None:
    """Print a compact StateBehavior summary for one state code."""
    behavior = get_state_behavior(state_code)
    print(f"StateBehavior({state_code}): {format_state_behavior(behavior, max_category_weights=max_category_weights)}")

#END