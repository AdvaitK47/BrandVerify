"""
Shared test setup.

The DATABASE_URL below MUST be set before any backend module is imported,
so tests use a throwaway database and never touch brandverify.db.
"""

import os
import tempfile

_TEST_DB_DIR = tempfile.mkdtemp(prefix="bv_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_DIR}/test.db"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    from backend.main import app
    from backend.api import verify

    # Replace the real AI call with a fixed answer: fast, free, predictable.
    monkeypatch.setattr(
        verify, "explain_findings", lambda text, flags: "TEST EXPLANATION"
    )

    with TestClient(app) as test_client:
        yield test_client
