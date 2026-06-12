import json
import logging
import os

logger = logging.getLogger(__name__)


def load_checkpoint(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_checkpoint(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def mark_done(path: str, indicator: str, s3_key: str) -> None:
    state = load_checkpoint(path)
    state[indicator] = {"status": "done", "s3_key": s3_key}
    save_checkpoint(path, state)
    logger.debug("checkpoint updated indicator=%s", indicator)


def is_done(path: str, indicator: str) -> bool:
    return load_checkpoint(path).get(indicator, {}).get("status") == "done"
