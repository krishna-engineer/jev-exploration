import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from recommender.call_log import call_logger
from recommender.judge import judge_task
from recommender.rank import recommend_model
from recommender.translate import judgements_to_requirement
from recommender.schemas import create_ranking_output

logger = logging.getLogger(__name__)
VALID_TASK_GATE_THRESHOLD = 0.7  # This is to handle greetings, chit-chats differently
INVALID_TASK_MESSAGE = (
    "This doesn't look like a task for an AI model. Describe what you want done, "
    "for example summarizing a document or writing code, and I'll recommend a model."
)


def check_task_validity(judgements: dict, threshold: float) -> bool:
    is_valid_task_score = judgements.get("is_valid_task", {}).get("noul", 0)
    return is_valid_task_score >= threshold


def recommend_for_task(task: str, model_catalog: list[dict]) -> dict:
    judgements, jev_meta = judge_task(task)

    is_valid_task = check_task_validity(judgements=judgements, threshold=VALID_TASK_GATE_THRESHOLD)
    if not is_valid_task:
        requirement = {}
        recommendation_result = create_ranking_output(recommendation=None, reason=INVALID_TASK_MESSAGE, ranked=[])
    else:
        requirement = judgements_to_requirement(judgements)
        recommendation_result = recommend_model(model_catalog, requirement)

    top_model = recommendation_result["recommendation"]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "judgements": judgements,
        "judge_meta": jev_meta,
        "requirement": requirement,
        "recommended_model": top_model["id"] if top_model else None,
        "ranked_models": [m["id"] for m in recommendation_result["ranked"]],
    }

    try:
        call_logger.info(json.dumps(record))
    except Exception:
        # A logging failure must never break a recommendation
        logger.warning("Could not write call record", exc_info=True)

    return {**recommendation_result, "requirement": requirement}


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    with open(ROOT / "model_catalog.json") as f:
        model_catalog = json.load(f)

    tasks = [
        "Hello, who built you?",
        "Write a Python function that parses a CSV file and returns the rows as dictionaries.",
        "Here is a screenshot of our dashboard. Describe what the chart shows and any anomalies.",
        "What is the capital of Australia?",
        "Prove that the sum of two even integers is even, and then generalize the proof to modular arithmetic.",
        "Classify 2 million customer support tickets into 12 categories as cheaply as possible.",
        "Act as a travel agent: search flights, compare hotel prices through the booking API, and book the best option.",
        "Write a 5,000-word long-form report on renewable energy trends from these 40 research papers.",
        "Live voice assistant that must reply to the caller in under a second.",
    ]
    for task in tasks[0:1]:
        result = recommend_for_task(task, model_catalog)
        print(task)
        print(f"  requirement: {result['requirement']}")
        print(f"  -> {result['reason']}")
        print()
