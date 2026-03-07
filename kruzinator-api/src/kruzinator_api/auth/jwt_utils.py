"""JWT helper utilities for image_demo.

Encapsulates JWK loading and jwt encode/decode helpers so the main
authentication module can remain focused on FastAPI concerns.
"""
from __future__ import annotations
import logging

import joserfc.jwt as jwt
import joserfc.jws as jws
import joserfc.jwk as jwk

from ..config import get_settings
import time
import uuid
from .. import schemas

settings = get_settings()

def _load_jwk() -> tuple[jwk.Key, str]:
    """Load the JWK signing key and determine the signing algorithm.

    Raises RuntimeError if required configuration is missing or the key
    cannot be imported.
    Returns (key, alg).
    """
    if not settings.auth.jwt_private_key:
        raise RuntimeError("JWT_PRIVATE_KEY not configured")
    try:
        key = jwk.ECKey.import_key(settings.auth.jwt_private_key, {"use": "sig"})
    except Exception as e:
        logging.exception("Failed to import JWK key: %s", e)
        raise RuntimeError("Failed to import JWK key") from e

    alg = jws.JWSRegistry.guess_alg(
        key, jws.JWSRegistry.Strategy.RECOMMENDED
    ) or ""
    return key, alg


# Load once on import; importing modules should raise early if config is invalid
try:
    key, alg = _load_jwk()
except Exception:
    # Re-raise so failures are explicit during startup
    raise


def jwt_encode(claims: dict, claims_registry: jwt.JWTClaimsRegistry) -> str:
    """Encode and sign a JWT using the configured key and algorithm.

    The provided claims dict is validated/used as-is. The caller is
    responsible for setting standard claims (iss, aud, exp, iat, nbf).
    """
    # Validate claims against the registry (if present)
    try:
        claims_registry.validate(claims)
    except Exception:
        # Let the caller observe validation errors (raise)
        raise
    return jwt.encode({"alg": alg, "typ": "JWT"}, claims, key)


def jwt_decode(token: str, claims_registry: jwt.JWTClaimsRegistry) -> dict:
    """Decode and validate a JWT, returning the claims dictionary.

    Raises the underlying Jose errors on invalid/expired tokens.
    """
    _jwt = jwt.decode(token, key, algorithms=[alg])
    # Validate claims structure
    try:
        claims_registry.validate(_jwt.claims)
    except Exception:
        raise
    return _jwt.claims

id_token_claims_registry = jwt.JWTClaimsRegistry(
    iss=jwt.ClaimsOption(essential=True, value=settings.auth.jwt_issuer),
    aud=jwt.ClaimsOption(essential=True, value=settings.auth.jwt_audience),
    id=jwt.ClaimsOption(essential=True),
    username=jwt.ClaimsOption(essential=True),
    email=jwt.ClaimsOption(essential=False, allow_blank=True),
    is_active=jwt.ClaimsOption(essential=True),
    is_admin=jwt.ClaimsOption(essential=True)
)

refresh_token_claims_registry = jwt.JWTClaimsRegistry(
    iss=jwt.ClaimsOption(essential=True, value=settings.auth.jwt_issuer),
    id=jwt.ClaimsOption(essential=True),
    jti=jwt.ClaimsOption(essential=True),  # unique token identifier
)


def get_public_jwks() -> dict:
    """Return a JWKS dict suitable for the `/api/auth/jwks` endpoint.

    Raises:
      LookupError: when public keys are not available (e.g., non-ES256 alg)
      RuntimeError: for key/configuration mismatches or missing public key
    """
    # Ensure key is ECKey
    if not isinstance(key, jwk.ECKey):
        raise RuntimeError("JWT key error.")
    ec_key: jwk.ECKey = key
    return {"keys": [ec_key.as_dict(private=False)]}


def compute_expiry(iat: int | None = None) -> int:
    """Compute the expiry (exp) claim as an integer timestamp.

    Uses the configured LOGIN_EXPIRE_HOURS/MINUTES/SECONDS from config.
    """
    iat = int(time.time()) if iat is None else int(iat)
    return iat + settings.auth.login_expire_seconds


def create_access_token(user: schemas.UserResponse, scopes: list[str]) -> tuple[str, int]:
    """Build and sign a JWT for the given user and scopes.

    Returns (token, exp_timestamp).
    The `user` can be a Pydantic model with attributes used below.
    """
    iat = int(time.time())
    exp = compute_expiry(iat)
    # Support UserResponse (Pydantic), dict-like, or ORM objects.
    if hasattr(user, "model_dump"):
        dumped = user.model_dump()
        username = dumped.get("anonnymous_name") or dumped.get("username")
        user_id = dumped.get("id")
        email = dumped.get("email")
        is_active = dumped.get("is_active", False)
        is_admin = dumped.get("is_admin", False)
    elif isinstance(user, dict):
        username = user.get("anonnymous_name") or user.get("username")
        user_id = user.get("id")
        email = user.get("email")
        is_active = user.get("is_active", False)
        is_admin = user.get("is_admin", False)
    else:
        username = getattr(user, "anonnymous_name", None) or getattr(user, "username", None)
        user_id = getattr(user, "id", None)
        email = getattr(user, "email", None)
        is_active = getattr(user, "is_active", False)
        is_admin = getattr(user, "is_admin", False)

    claims = {
        "sub": username,
        "aud": settings.auth.jwt_audience,
        "scopes": ' '.join(scopes),
        "exp": exp,
        "iat": iat,
        "nbf": iat,
        "iss": settings.auth.jwt_issuer,
        "id": str(user_id) if user_id is not None else None,
        "username": username,
        "email": email,
        "is_active": is_active,
        "is_admin": is_admin,
    }
    token = jwt_encode(claims, id_token_claims_registry)
    return token, exp


def create_refresh_token(user: schemas.UserResponse) -> tuple[str, uuid.UUID]:
    """Create a refresh JWT containing only jti, id, iat and nbf (no exp).

    Returns (token, jti).
    """

    iat = int(time.time())
    if hasattr(user, "model_dump"):
        user_id = user.model_dump().get("id")
    elif isinstance(user, dict):
        user_id = user.get("id")
    else:
        user_id = getattr(user, "id", None)

    jti = uuid.uuid4()
    claims = {
        "jti": jti.hex,
        "iat": iat,
        "nbf": iat,
        "iss": settings.auth.jwt_issuer,
        "id": str(user_id) if user_id is not None else None,
    }

    # Bypass the claims_registry validation and sign directly
    token = jwt_encode(claims, refresh_token_claims_registry)
    return token, jti


def check_scope(requested_scopes: list[str], claims: dict[str, str] | schemas.UserResponse) -> bool:
    if isinstance(claims, schemas.UserResponse):
        claims = claims.model_dump()
    if "admin" in requested_scopes and not bool(claims.get("is_admin", False)):
        return False
    if "annotations" in requested_scopes and not bool(claims.get("is_active", False)):
        return False
    if "me" in requested_scopes and not bool(claims.get("is_active", False)):
        return False
    return True

