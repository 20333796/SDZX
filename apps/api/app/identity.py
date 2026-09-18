from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Callable

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class Role(str, Enum):
    learner = "learner"
    teacher = "teacher"
    admin = "admin"


@dataclass(frozen=True)
class Principal:
    subject: str
    name: str | None
    roles: frozenset[Role]


class OIDCVerifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    def verify(self, token: str) -> Principal:
        if not self.settings.oidc_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="School OIDC is not configured",
            )
        jwks_url = self.settings.oidc_jwks_url or f"{self.settings.oidc_issuer.rstrip('/')}/.well-known/jwks.json"
        try:
            signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=self.settings.oidc_audience,
                issuer=self.settings.oidc_issuer,
            )
        except jwt.PyJWTError as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OIDC access token") from error

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC token has no subject")
        raw_roles = claims.get(self.settings.oidc_role_claim, [])
        if isinstance(raw_roles, str):
            raw_roles = [raw_roles]
        roles = frozenset(Role(role) for role in raw_roles if role in Role._value2member_map_)
        return Principal(subject=subject, name=claims.get("name"), roles=roles or frozenset({Role.learner}))


class GeoChatVerifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def verify(self, token: str) -> Principal:
        base_url = self.settings.geochat_auth_bridge_url
        if not base_url:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GeoChat login is not configured")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{base_url.rstrip('/')}/api/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GeoChat identity service is unavailable",
            ) from error

        if response.status_code in (401, 403):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid GeoChat access token")
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GeoChat identity service is unavailable")

        payload = response.json()
        subject = payload.get("uid")
        name = payload.get("username")
        if not isinstance(subject, str) or not subject:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GeoChat identity has no subject")
        if not isinstance(name, str) or not name:
            name = None

        role = payload.get("role")
        roles = frozenset({Role.admin}) if role in {"admin", "superadmin"} else frozenset({Role.learner})
        return Principal(subject=subject, name=name, roles=roles)


@lru_cache
def get_oidc_verifier() -> OIDCVerifier:
    return OIDCVerifier(get_settings())


async def get_current_principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login is required")

    settings = get_settings()
    if settings.oidc_enabled:
        try:
            return get_oidc_verifier().verify(credentials.credentials)
        except HTTPException as error:
            if error.status_code != status.HTTP_401_UNAUTHORIZED or not settings.geochat_auth_bridge_enabled:
                raise

    if settings.geochat_auth_bridge_enabled:
        return await GeoChatVerifier(settings).verify(credentials.credentials)

    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="School OIDC is not configured")


def require_roles(*required_roles: Role) -> Callable[[Principal], Principal]:
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not set(required_roles).intersection(principal.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency
