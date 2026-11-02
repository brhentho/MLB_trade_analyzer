import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def _no_openai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app import ratelimit

    ratelimit.reset()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import create_app

    return TestClient(create_app())


@pytest.fixture()
def store():
    from app.store import get_store

    return get_store()
