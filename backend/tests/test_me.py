"""Tests for GET /api/me endpoint."""
import os
from unittest.mock import MagicMock, patch

import pytest

# Patch DB engine creation before any app import so tests don't need a real DB
_mock_engine = MagicMock()
_mock_engine.dispose = MagicMock(return_value=None)

with (
    patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=_mock_engine),
    patch.dict(os.environ, {"DATABASE_URL": "mssql+aioodbc://x:y@localhost/db"}),
):
    from app.main import create_app
    from app import auth


def _make_client(user_payload: dict | None = None):
    app = create_app()
    if user_payload is not None:
        app.dependency_overrides[auth.get_current_user] = lambda: user_payload
    from fastapi.testclient import TestClient
    return TestClient(app, raise_server_exceptions=False)


def test_me_returns_jwt_payload():
    """/api/me returns the decoded JWT payload for an authenticated request."""
    payload = {"sub": "user-abc", "preferred_username": "bob"}
    client = _make_client(user_payload=payload)
    resp = client.get("/api/me")
    assert resp.status_code == 200
    assert resp.json() == payload


def test_me_without_auth_returns_401():
    """/api/me returns 401 when no Authorization header is provided."""
    client = _make_client()
    resp = client.get("/api/me")
    assert resp.status_code == 401
