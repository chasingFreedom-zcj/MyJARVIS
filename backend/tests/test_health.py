from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.routers import health


def test_liveness_returns_service_information(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "MyJARVIS",
        "version": "0.1.0",
    }


def test_readiness_returns_ok_when_dependencies_are_available(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def check_ok() -> None:
        return None

    monkeypatch.setattr(health, "_check_database", check_ok)
    monkeypatch.setattr(health, "_check_redis", check_ok)

    response = client.get("health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "database": {"status": "ok"},
            "redis": {"status": "ok"},
        },
    }


def test_readiness_returns_503_when_redis_is_not_available(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def check_database() -> None:
        return None

    async def check_redis() -> None:
        raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(health, "_check_database", check_database)
    monkeypatch.setattr(health, "_check_redis", check_redis)

    response = client.get("health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "checks": {
            "database": {"status": "ok"},
            "redis": {"status": "unavailable"},
        },
    }
