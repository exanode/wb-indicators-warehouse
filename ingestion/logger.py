import json
import logging
import os
import sys
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        skip = set(logging.LogRecord.__dict__) | {"msg", "args", "message"}
        for k, v in record.__dict__.items():
            if k not in skip:
                base[k] = v
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, default=str)


def setup_logging(log_path: str = None, level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        handlers.append(logging.FileHandler(log_path))
    fmt = StructuredFormatter()
    for h in handlers:
        h.setFormatter(fmt)
        root.addHandler(h)
