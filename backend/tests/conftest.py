import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://myjarvis:majarvis_dev@127.0.0.1:5432/myjarvis",
)
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
