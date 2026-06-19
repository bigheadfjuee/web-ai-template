"""Tests for backend/app/auth.py — JWT validation dependency."""
import importlib
import os
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_signing_key(decoded_payload: dict):
    """Return a mock signing key whose data attribute satisfies PyJWT decode."""
    key = MagicMock()
    # PyJWT's decode() accepts a key object; we'll patch jwt.decode directly
    key.key = "mock-key"
    return key


# ---------------------------------------------------------------------------
# Module-level env var test
# ---------------------------------------------------------------------------

def test_default_jwks_uri():
    """KEYCLOAK_JWKS_URI defaults to Keycloak's JWKS path when env var is absent."""
    env = os.environ.copy()
    env.pop("KEYCLOAK_JWKS_URI", None)
    with patch.dict(os.environ, env, clear=True):
        import importlib
        import app.auth as auth_mod
        importlib.reload(auth_mod)
        assert auth_mod.KEYCLOAK_JWKS_URI == (
            "http://keycloak:8080/auth/realms/app/protocol/openid-connect/certs"
        )


def test_custom_jwks_uri_from_env():
    """KEYCLOAK_JWKS_URI is read from environment when set."""
    custom = "http://custom-keycloak/certs"
    with patch.dict(os.environ, {"KEYCLOAK_JWKS_URI": custom}):
        import importlib
        import app.auth as auth_mod
        importlib.reload(auth_mod)
        assert auth_mod.KEYCLOAK_JWKS_URI == custom


# ---------------------------------------------------------------------------
# get_current_user — success path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """get_current_user returns decoded payload for a valid Bearer token."""
    payload = {"sub": "user-123", "preferred_username": "alice"}
    mock_key = MagicMock()
    mock_key.key = "some-key"

    import app.auth as auth_mod

    with (
        patch.object(auth_mod._jwks_client, "get_signing_key_from_jwt", return_value=mock_key),
        patch("jwt.decode", return_value=payload),
    ):
        result = await auth_mod.get_current_user(token="fake.jwt.token")

    assert result == payload


# ---------------------------------------------------------------------------
# get_current_user — failure paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_invalid_token_raises_401():
    """get_current_user raises HTTP 401 when JWKS key lookup fails."""
    import app.auth as auth_mod

    with patch.object(
        auth_mod._jwks_client,
        "get_signing_key_from_jwt",
        side_effect=Exception("Key not found"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await auth_mod.get_current_user(token="bad.token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token"


@pytest.mark.asyncio
async def test_get_current_user_expired_token_raises_401():
    """get_current_user raises HTTP 401 when jwt.decode raises DecodeError."""
    import app.auth as auth_mod
    mock_key = MagicMock()
    mock_key.key = "k"

    with (
        patch.object(auth_mod._jwks_client, "get_signing_key_from_jwt", return_value=mock_key),
        patch("jwt.decode", side_effect=jwt.ExpiredSignatureError("expired")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await auth_mod.get_current_user(token="expired.jwt.token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_token_raises_401():
    """get_current_user raises HTTP 401 when token is empty string."""
    import app.auth as auth_mod

    with patch.object(
        auth_mod._jwks_client,
        "get_signing_key_from_jwt",
        side_effect=Exception("bad token"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await auth_mod.get_current_user(token="")

    assert exc_info.value.status_code == 401
