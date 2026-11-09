import logging
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "judgments.jsonl"

# One JSON line per recommendation call. propagate=False keeps these lines out of the root logger (terminal output).
call_logger = logging.getLogger("recommender.calls")
call_logger.setLevel(logging.INFO)
call_logger.propagate = False

if not call_logger.handlers:
    LOG_PATH.parent.mkdir(exist_ok=True)
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8", delay=True)
    handler.setFormatter(logging.Formatter("%(message)s"))
    call_logger.addHandler(handler)
