from ..config import Settings, get_settings
from fastapi import Depends
from fastapi import APIRouter

well_known_router = APIRouter(prefix="/.well-known", tags=["well-known"])

@well_known_router.get("/openid-configuration")
async def get_openid_configuration(
    settings: Settings = Depends(get_settings)
) -> dict:
    """Get OpenID Connect configuration."""
    
    return {
        "issuer": settings.auth.jwt_issuer,
        "authorization_endpoint": f"{settings.auth.jwt_issuer}/api/v1/auth/login",
        "token_endpoint": f"{settings.auth.jwt_issuer}/api/v1/auth/token",
        "userinfo_endpoint": f"{settings.auth.jwt_issuer}/api/v1/users/me",
        "jwks_uri": f"{settings.auth.jwt_issuer}/api/v1/auth/jwks",
        "response_types_supported": ["access_token", "refresh_token"],
        "grant_types_supported": [
            "authorization_code"
        ],
        "claim_types_supported": ["normal"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["ES256"],
        "scopes_supported": ["me", "annotations", "admin"],
    }
