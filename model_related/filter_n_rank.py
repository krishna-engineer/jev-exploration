from datetime import date
from pathlib import Path
import json

# requirement key -> catalog field. 
# 
# A boolean rule keeps models where the field is True.
BOOLEAN_RULES = {
    "tool_call": "tool_call",
    "structured_output": "structured_output",
    "needs_reasoning": "reasoning",
}
# A minimum rule keeps models where the field is >= the requirement value.
MIN_RULES = {
    "min_context": "context",
    "min_output": "max_output",
}
# A maximum rule keeps models where the field is <= the requirement value (price caps, $ per 1M tokens).
MAX_RULES = {
    "max_price_in": "price_in",
    "max_price_out": "price_out",
}
PRICE_IN_WEIGHT = 1
PRICE_OUT_WEIGHT = 1
# Age used when release_date is missing (~10 years). Must exceed any real model's age so undated models lose ties.
UNKNOWN_AGE_DAYS = 3650

def get_age_in_days(release_date: str | None) -> int:
    if not release_date:
        return UNKNOWN_AGE_DAYS
    d = date.fromisoformat(release_date)
    return (date.today() - d).days 



def filter_models(model_catalog: list[dict], requirement: dict) -> list[dict]:
    model_type = requirement.get("model_type", "chat") # By default, chat (not embeddings or other) models are chosen

    model_catalog_filtered = [m for m in model_catalog if m['price_in'] > 0 and m['price_out'] > 0]
    model_catalog_filtered = [m for m in model_catalog_filtered if m['model_type'] == model_type]
    
    if requirement.get("vision", False) is True:
        model_catalog_filtered = [m for m in model_catalog_filtered if "image" in m['input_modalities']]

    for requirement_key, field in BOOLEAN_RULES.items():
        if requirement.get(requirement_key):
            model_catalog_filtered = [m for m in model_catalog_filtered if m[field]]

    for requirement_key, field in MIN_RULES.items():
        value = requirement.get(requirement_key)
        if value is not None:
            model_catalog_filtered = [m for m in model_catalog_filtered if m[field] >= value]

    for requirement_key, field in MAX_RULES.items():
        value = requirement.get(requirement_key)
        if value is not None:
            model_catalog_filtered = [m for m in model_catalog_filtered if m[field] <= value]

    return model_catalog_filtered


def rank_models(model_catalog: list[dict], requirement: dict, num_models_to_return=3) -> list[dict]:
    price_sign = -1 if requirement.get("cost_preference", "") == "premium" else 1

    # Ascending sort: price (flipped for premium), then newest, then largest context.
    model_catalog_ranked = sorted(model_catalog,
                                  key=lambda m: (price_sign * (PRICE_IN_WEIGHT* m['price_in'] + PRICE_OUT_WEIGHT* m['price_out']),
                                                 get_age_in_days(m['release_date']),
                                                 -m['context']))


    return model_catalog_ranked[0: num_models_to_return]


def build_reason(model: dict, pool_size: int, cost_preference: str = "cheapest") -> str:
    is_premium = cost_preference == "premium"
    superlative = "Costliest" if is_premium else "Cheapest"

    reason = (f"{superlative} of {pool_size} matching models: {model['name']} ({model['provider']}), "
              f"${model['price_in']} in / ${model['price_out']} out per 1M tokens.")

    if is_premium:
        reason += " Premium means highest price, not proven best quality."

    return reason


def recommend_model(model_catalog: list[dict], requirement: dict) -> dict:
    model_catalog_filtered = filter_models(model_catalog, requirement)

    if not model_catalog_filtered:
        return {"recommendation": None,
                "reason": "No model meets these requirements.",
                "ranked": []}

    ranked = rank_models(model_catalog_filtered, requirement)
    cost_preference = requirement.get("cost_preference", "cheapest")

    reason = build_reason(ranked[0], len(model_catalog_filtered), cost_preference)

    return {"recommendation": ranked[0],
            "reason": reason,
            "ranked": ranked}


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    CATALOG_PATH = ROOT / "model_catalog.json"
    with open(CATALOG_PATH) as f:
        model_catalog = json.load(f)

    requirements = [
        {},
        {"cost_preference": "premium"},
        {"vision": True},
        {"vision": True, "min_context": 500000},
        {"needs_reasoning": True},
        {"needs_reasoning": True, "cost_preference": "premium"},
        {"tool_call": True, "structured_output": True},
        {"min_output": 100000},
        {"max_price_in": 1, "max_price_out": 5},
        {"vision": True, "needs_reasoning": True, "min_context": 1000000, "cost_preference": "premium"},
        {"min_context": 99999999},  # impossible: expect "No model meets these requirements."
    ]

    for requirement in requirements:
        result = recommend_model(model_catalog, requirement)
        print(requirement)
        print(f"  -> {result['reason']}")
