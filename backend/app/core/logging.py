import json
import logging
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    extra_fields = (
        "event",
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "dependency",
        "error_type",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in self.extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


_logging_configured = False


def configure_logging(log_level: str) -> None:
    global _logging_configured

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    if not _logging_configured:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root_logger.handlers = [handler]
        _logging_configured = True

    logging.getLogger("uvicorn.access").disabled = True
