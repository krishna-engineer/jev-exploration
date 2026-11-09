"""Shapes of the data that cross module boundaries (the recommendation result)."""


def create_ranking_output(*, recommendation: dict | None, reason: str, ranked: list[dict]) -> dict:
    # The only place the result keys are written. recommendation is None when no model is recommended.
    return {
        "recommendation": recommendation,
        "reason": reason,
        "ranked": ranked,
    }
