"""conftest.py — hermetische testopstelling (tijdelijke SQLite + ingelogde admin)."""
import os
import tempfile

import pytest

_fd, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ.setdefault("RHADIX_ADMIN_EMAIL", "admin@rhadix.nl")
os.environ.setdefault("RHADIX_ADMIN_PASSWORD", "Rhadixcrm26!")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app                   # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    try:
        os.unlink(_DB_PATH)
    except OSError:
        pass


@pytest.fixture(scope="session")
def auth(client):
    r = client.post("/api/auth/login",
                    json={"email": "admin@rhadix.nl", "password": "Rhadixcrm26!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
