import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWKClient

KEYCLOAK_JWKS_URI: str = os.environ.get(
    "KEYCLOAK_JWKS_URI",
    "http://keycloak:8080/auth/realms/app/protocol/openid-connect/certs",
)

_jwks_client = PyJWKClient(KEYCLOAK_JWKS_URI)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
