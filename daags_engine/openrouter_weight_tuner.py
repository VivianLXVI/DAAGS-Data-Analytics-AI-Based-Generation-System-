"""
OpenRouter-based weight tuner.

This module is intentionally optional and disabled by default.
If enabled via environment variables, it can request adjusted state/category
weights from OpenRouter and return them as a JSON-compatible dict.
"""

import json
import urllib.request
from typing import Any, Dict, List, Optional

from daags_engine.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)


def _extract_json(text: str) -> str:
    """
    Try to extract the first JSON object from a model response.
    This makes parsing more robust when the response contains extra text.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find JSON object in OpenRouter response.")
    return text[start : end + 1]


def request_state_weight_overrides(
    base_state_behavior: Dict[str, Dict[str, Any]],
    user_instruction: str,
    active_states: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Ask OpenRouter for updated state weights.

    base_state_behavior:
      Mapping: state_code -> dict of current values.

    user_instruction:
      English instruction describing how the dataset should change (e.g.
      "make winter slow down sales").

    active_states:
      Optional list of state codes to tune. If provided, only those states
      are included in the prompt payload (matched case-insensitively). If
      filtering results in an empty set, all states from base_state_behavior
      are used as a fallback.

    Returns:
      A dict expected to be JSON-compatible.
      The caller is responsible for validating fields and applying them.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is empty; cannot call OpenRouter.")

    # Optionally filter the base behavior down to the active subset to reduce payload size.
    states_payload: Dict[str, Dict[str, Any]] = base_state_behavior
    if active_states:
        allowed = {code.strip().upper() for code in active_states if code}
        filtered = {
            code: behavior
            for code, behavior in base_state_behavior.items()
            if code.upper() in allowed
        }
        if filtered:
            states_payload = filtered

    system = (
        "You are tuning synthetic retail purchase behavior for a dataset. "
        "Your goal is to return aggressive, instruction-following adjustments to "
        "per-state purchase behavior weights.\n\n"
        "Constraints:\n"
        "- Keep min_items and max_items within [1, 10] and ensure max_items >= min_items.\n"
        "- Ensure category_weights has non-negative numeric weights. Do not output empty weights.\n"
        "- Ensure payment_method_weights has non-negative numeric weights for card/cash/online.\n"
        "- Keep price_spread within [0.0, 0.2].\n"
        "- Ensure month_item_multiplier has numeric multipliers for months \"1\"..\"12\".\n"
        "- Keep month_item_multiplier values within [0.2, 2.0].\n"
        "- Only adjust weights; do not change state codes.\n"
        "- If the instruction specifies a percentage or numeric increase/decrease "
        "for purchase frequency or seasonality (month-level effects), you MUST move "
        "purchase_freq_factor and month_item_multiplier values by approximately that "
        "magnitude rather than making tiny token adjustments.\n"
        "- Output MUST be valid JSON and nothing else."
    )

    user_context = {
        "task": "Given base per-state behavior parameters, return tuned overrides that satisfy the instruction.",
        "input": {
            "states": states_payload,
        },
        "output_schema": {
            "overrides": {
                "STATE_CODE": {
                    "purchase_freq_factor": 1.0,
                    "min_items": 1,
                    "max_items": 5,
                    "category_weights": {"gaming": 1.0, "tech": 1.0},
                    "payment_method_weights": {"card": 0.4, "cash": 0.2, "online": 0.4},
                    "price_spread": 0.05,
                    "month_item_multiplier": {
                        "1": 1.0,
                        "2": 1.0,
                        "3": 1.0,
                        "4": 1.0,
                        "5": 1.0,
                        "6": 1.0,
                        "7": 1.0,
                        "8": 1.0,
                        "9": 1.0,
                        "10": 1.0,
                        "11": 1.0,
                        "12": 1.0,
                    },
                }
            }
        },
    }

    user_message = (
        f"INSTRUCTION: {user_instruction.strip() if user_instruction else ''}\n\n"
        "CONTEXT:\n"
        + json.dumps(user_context, indent=2)
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
    }

    req = urllib.request.Request(
        url="https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8")

    parsed = json.loads(raw)
    content = parsed["choices"][0]["message"]["content"]
    # # Print for debugging purposes
    # with open(r'C:\Programming\mnsu\2026_spring\synthetic_data\private_github_repo\DAAGS-research-project\daags_engine\outputs\response.md', "w") as f:
    #     # 'indent=4' creates the clean indentation
    #     f.write(str(content).replace("\\n", "\n").replace(r'\"', '"'))
    json_text = _extract_json(content)
    return json.loads(json_text)

