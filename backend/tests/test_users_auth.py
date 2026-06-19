"""Tests verifying /api/users routes require authentication."""
import os
from unittest.mock import MagicMock, patch

_mock_engine = MagicMock()
_mock_engine.dispose = MagicMock(return_value=None)

with (
    patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=_mock_engine),
    patch.dict(os.environ, {"DATABASE_URL": "mssql+aioodbc://x:y@localhost/db"}),
):
    from app.main import create_app
    from app import auth

from fastapi.testclient import TestClient


def _client_no_auth():
    """TestClient with no auth override — get_current_user raises 401."""
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def _client_with_auth():
    """TestClient with get_current_user overridden to succeed."""
    app = create_app()
    app.dependency_overrides[auth.get_current_user] = lambda: {"sub": "user-1"}
    return TestClient(app, raise_server_exceptions=False)


def test_list_users_without_auth_returns_401():
    """GET /api/users requires authentication."""
    resp = _client_no_auth().get("/api/users")
    assert resp.status_code == 401


def test_create_user_without_auth_returns_401():
    """POST /api/users requires authentication."""
    resp = _client_no_auth().post("/api/users", json={"username": "x", "email": "x@x.com"})
    assert resp.status_code == 401


def test_health_is_public():
    """/api/health is accessible without authentication."""
    resp = _client_no_auth().get("/api/health")
    assert resp.status_code == 200
