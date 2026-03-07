"""Authentication module for image_demo_backend.

This file exposes FastAPI auth dependencies and the auth router.
JWT encode/decode and JWK loading are delegated to
``image_demo.auth.jwt_utils``.
"""
from joserfc import jwk as jwk
import uuid
import logging
from typing import Annotated
from sqlalchemy import select, update
from typing_extensions import Doc
import fastapi
from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Response, Security
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from pydantic import ValidationError

from joserfc.errors import JoseError, ExpiredTokenError

from ..auth.password_utils import check_password, hash_password

from ..auth.jwt_utils import (
    create_refresh_token,
    jwt_decode,
    id_token_claims_registry,
    refresh_token_claims_registry,
    create_access_token,
    get_public_jwks,
    check_scope
)

from .. import schemas
from .. import models
from ..config import Settings, get_settings
from ..db import AsyncSession, get_db_session

__all__ = [
    "auth_router",
    "get_current_user",
    "get_current_active_user",
]


auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    refreshUrl="/api/v1/auth/refresh",
    scopes={
        "me": "Read information about the current user.",
        "annotations": "Read, write, edit, delete annotations.",
        "admin": "Admin access."
    }
)

async def validate_token(
    security_scopes: SecurityScopes, 
    token: str = Depends(oauth2_scheme)
) -> dict[str, str]:
    credentials_exception = HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    permission_exception = HTTPException(
        status_code=fastapi.status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
        headers={"WWW-Authenticate": "Bearer"},
    )
    timeout_exception = HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Access token has expired",
    )
    try:
        claims: dict[str, str] = jwt_decode(token, id_token_claims_registry)
    except ExpiredTokenError:
        logging.error("JWT token has expired")
        raise timeout_exception
    except JoseError as e:
        logging.error(f"Failed to decode JWT token: {e}")
        raise credentials_exception
    except ValidationError as e:
        logging.error(f"Failed to validate JWT token claims: {e}")
        raise credentials_exception
    scopes = claims.get("scopes", "").split(' ')
    if set(security_scopes.scopes).difference(set(scopes)):
        raise permission_exception
    if not check_scope(security_scopes.scopes, claims):
        raise permission_exception
    return claims


async def get_current_user(
    claims: dict[str, str] = Security(
        validate_token, scopes=[]
    )
) -> schemas.UserResponse:
    try:
        user = schemas.UserResponse.model_validate(claims)
    except ValidationError as e:
        logging.error(f"Failed to validate user from JWT claims: {e}")
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: schemas.UserResponse = Security(
        get_current_user, 
        scopes=["me"]
    )
) -> schemas.UserResponse:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class OAuth2RefreshRequestForm:
    def __init__(
        self,
        grant_type: Annotated[
            str | None,
            Form(pattern="^refresh_token$"),
            Doc("Must be 'refresh_token'")
        ] = None,
        refresh_token: Annotated[
            str | None,
            Form(),
            Doc("The refresh token issued to the client.")
        ] = None,
        scope: Annotated[
            str,
            Form(),
            Doc("The scope of the access request.")
        ] = "",
    ):
        self.grant_type = grant_type or "refresh_token"
        self.refresh_token = refresh_token
        self.scopes = scope.split()


@auth_router.post("/register", response_model=schemas.TokenResponse)
async def register(
    payload: schemas.RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> schemas.TokenResponse:
    existing = (
        await db.execute(select(models.User).where(models.User.anonnymous_name == payload.username))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = models.User(
        id=uuid.uuid4(),
        anonnymous_name=payload.username,
        hashed_password=hash_password(payload.password),
        refresh_token_jti=None,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_schema = schemas.UserResponse.model_validate(user)

    scopes = ["me"]
    access_token, _expire = create_access_token(user_schema, scopes)
    refresh_jwt_token, jti = create_refresh_token(user_schema)

    await db.execute(
        update(models.User)
        .where(models.User.id == user.id)
        .values(refresh_token_jti=jti)
    )
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=refresh_jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )

    logging.info(f"Registered user '{payload.username}'")
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_jwt_token,
        token_type="bearer",
    )


@auth_router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    response: Response,
    form_data: OAuth2RefreshRequestForm = Depends(),
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db_session)
) -> schemas.TokenResponse:
    refresh_token = form_data.refresh_token or refresh_token_cookie
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh token")
    try:
        refresh_token_claims: dict[str, str] = jwt_decode(
            refresh_token, refresh_token_claims_registry
        )
    except ExpiredTokenError as e:
        logging.error(f"Refresh token has expired: {e}")
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except JoseError as e:
        logging.error(f"Failed to decode refresh token: {e}")
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    if not refresh_token_claims.get("id"):
        logging.error("Refresh token missing user ID")
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user_id = uuid.UUID(refresh_token_claims.get("id", None))
    if not user_id:
        logging.error(
            f"Invalid user ID in refresh token: {refresh_token_claims.get('id')}")
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = await db.get(models.User, user_id)
    if not user:
        logging.error(f"User not found: {user_id}")
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_schema = schemas.UserResponse.model_validate(user)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not check_scope(refresh_token_claims.get("scopes", "").split(' '), user_schema):
        logging.info(
            f"User '{user_schema.username}' does not have the required scopes: {form_data.scopes}"
        )
        raise HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="You don't have the required permissions for the requested scopes"
        )
    jti = refresh_token_claims.get("jti")
    if not jti:
        logging.error("Refresh token missing JTI")
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    jti_uuid = uuid.UUID(jti)
    if not user.refresh_token_jti == jti_uuid:
        await db.execute(
            update(models.User).where(models.User.id == user.id).values(refresh_token_jti=None)
        )
        await db.commit()
        logging.error(
            f"Refresh token JTI does not match: {user.refresh_token_jti} != {jti_uuid}"
        )
        raise HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # build token using helper
    scope = sorted(set(form_data.scopes + ["me"]))
    jwt_token, expire = create_access_token(user_schema, scope)
    refresh_jwt_token, new_jti = create_refresh_token(user_schema)
    await db.execute(
        update(models.User).where(models.User.id == user.id).values(refresh_token_jti=new_jti)
    )
    await db.commit()

    # Rotate the cookie too (if the client uses cookies)
    response.set_cookie(
        key="refresh_token",
        value=refresh_jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    # token was created above by create_access_token
    logging.info(
        f"User '{user_schema.username}' renewed token successfully with scopes: {scope} expire: {expire} and refresh token: {refresh_jwt_token}"
    )
    return schemas.TokenResponse(
        access_token=jwt_token,
        refresh_token=refresh_jwt_token,
        token_type="bearer"
    )


@auth_router.post("/token", response_model=schemas.TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
) -> schemas.TokenResponse:
    form_data.grant_type
    user = (await db.execute(select(models.User).where(models.User.anonnymous_name == form_data.username))).scalars().first()
    if not user:
        logging.info(f"User '{form_data.username}' not found")
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    user_schema = schemas.UserResponse.model_validate(user)
    # validate password
    if not user.hashed_password:
        logging.info(f"User '{form_data.username}' does not have a password set")
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    if not check_password(form_data.password, user.hashed_password):
        logging.info(
            f"Invalid password attempt for user '{form_data.username}'"
        )
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    # check scopes (always require at least 'me')
    requested_scopes = sorted(set(form_data.scopes + ["me"]))
    if not check_scope(requested_scopes, user_schema):
        logging.info(
            f"User '{form_data.username}' does not have the required scopes: {requested_scopes}"
        )
        raise HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="You don't have the required permissions for the requested scopes"
        )
    jwt_token, expire = create_access_token(user_schema, requested_scopes)
    refresh_token, jti = create_refresh_token(user_schema)
    await db.execute(
        update(models.User).where(models.User.id == user.id).values(refresh_token_jti=jti)
    )
    await db.commit()
    logging.info(
        f"User '{form_data.username}' logged in successfully with scopes: {requested_scopes} expire: {expire} and refresh token: {str(jti)}"
    )
    return schemas.TokenResponse(
        access_token=jwt_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@auth_router.get("/jwks")
async def get_public_key() -> dict:
    """Get the public key for JWT verification."""
    try:
        return get_public_jwks()
    except LookupError:
        # Not available (e.g. non-ES256)
        raise HTTPException(
            status_code=404, detail="JWT public keys are not available.")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


