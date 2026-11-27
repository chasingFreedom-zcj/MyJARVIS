import json
import logging

from fastapi.testclient import TestClient
from pytest import LogCaptureFixture

from app.core.logging import JsonFormatter


def test_json_formatter_outputs_structured_log() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    record.__dict__["event"] = "test_event"
    record.__dict__["request_id"] = "test-request"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "test message"
    assert payload["event"] == "test_event"
    assert payload["request_id"] == "test-request"


def test_request_completion_is_logged(
    client: TestClient,
    caplog: LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/health/live",
            headers={"X-Request-Id": "test-request-123"},
        )

    assert response.headers["X-Request-Id"] == "test-request-123"

    request_log = next(
        record for record in caplog.records if getattr(record, "event", None) == "request_completed"
    )
    assert request_log.request_id == "test-request-123"
    assert request_log.method == "GET"
    assert request_log.path == "/health/live"
    assert request_log.status_code == 200
