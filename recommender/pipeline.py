import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from recommender.call_log import call_logger
from recommender.judge import judge_task
from recommender.rank import recommend_model
from recommender.translate import judgments_to_requirement

logger = logging.getLogger(__name__)


def recommend_for_task(task: str, model_catalog: list[dict]) -> dict:
    judgments, jev_meta = judge_task(task)
    requirement = judgments_to_requirement(judgments)
    recommendation = recommend_model(model_catalog, requirement)

    top_model = recommendation["recommendation"]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "judgments": judgments,
        "judge_meta": jev_meta,
        "requirement": requirement,
        "recommended_model": top_model["id"] if top_model else None,
        "ranked_models": [m["id"] for m in recommendation["ranked"]],
    }

    try:
        call_logger.info(json.dumps(record))
    except Exception:
        # A logging failure must never break a recommendation
        logger.warning("Could not write call record", exc_info=True)

    return {**recommendation, "requirement": requirement}


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    with open(ROOT / "model_catalog.json") as f:
        model_catalog = json.load(f)

    tasks = [
        "Write a Python function that parses a CSV file and returns the rows as dictionaries.",
        "Here is a screenshot of our dashboard. Describe what the chart shows and any anomalies.",
        "What is the capital of Australia?",
        "Prove that the sum of two even integers is even, and then generalize the proof to modular arithmetic.",
        "Classify 2 million customer support tickets into 12 categories as cheaply as possible.",
        "Act as a travel agent: search flights, compare hotel prices through the booking API, and book the best option.",
        "Write a 5,000-word long-form report on renewable energy trends from these 40 research papers.",
        "Live voice assistant that must reply to the caller in under a second.",
    ]
    for task in tasks[0:3]:
        result = recommend_for_task(task, model_catalog)
        print(task)
        print(f"  requirement: {result['requirement']}")
        print(f"  -> {result['reason']}")
        print()

