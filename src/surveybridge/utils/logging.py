"""Structured diagnostics on stderr; no request headers or credentials are logged."""

import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            },
            ensure_ascii=False,
        )


def configure_logging():
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=logging.WARNING, handlers=[handler], force=True)
