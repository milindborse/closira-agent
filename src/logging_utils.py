import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Optional


_LOGGER: Optional[logging.Logger] = None


def _log_dir() -> str:
    return os.environ.get("CLOSIRA_LOG_DIR", "logs")


def ensure_log_dir() -> str:
    path = _log_dir()
    os.makedirs(path, exist_ok=True)
    return path


def get_logger() -> logging.Logger:
    """App logger with console + rotating file handlers (idempotent)."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    ensure_log_dir()

    logger = logging.getLogger("closira")
    logger.setLevel(os.environ.get("CLOSIRA_LOG_LEVEL", "INFO").upper())
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console = logging.StreamHandler()
        console.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            os.path.join(_log_dir(), "app.log"),
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(console)
        logger.addHandler(file_handler)

    _LOGGER = logger
    return logger


def append_jsonl(filename: str, record: dict[str, Any]) -> None:
    """Append a single JSON record to a JSONL file in the log dir."""
    ensure_log_dir()
    path = os.path.join(_log_dir(), filename)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_event(event: str, payload: dict[str, Any]) -> None:
    logger = get_logger()
    logger.info("event=%s", event)
    append_jsonl(
        "events.jsonl",
        {
            "event": event,
            **payload,
        },
    )
