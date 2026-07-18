"""Authentication helpers for the EcoTrace dashboard.

Authentication is OAuth-only (Google and GitHub).
Password-based sign-up and login are not supported.
"""
import hashlib
import secrets
import time
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from config import settings
from database import User, database, initialize_development_database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")
oauth = OAuth()

if settings.google_oauth_configured:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if settings.github_oauth_configured:
    oauth.register(
        name="github",
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "read:user user:email"},
    )


def initialize_database() -> None:
    initialize_development_database()


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = int(time.time() + settings.access_token_expire_minutes * 60)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def get_current_user_from_token(token: str) -> dict:
    payload = decode_access_token(token)
    email = payload.get("sub") if payload else None
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    with database() as db:
        user = db.get(User, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return {
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at,
        "api_key_hash": user.api_key_hash,
    }


def new_ingestion_key() -> str:
    return "ect_" + secrets.token_urlsafe(32)


def hash_ingestion_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _create_oauth_user(email: str, name: str, oauth_provider: str) -> None:
    """Create a new OAuth user with a fresh ingestion key."""
    key = new_ingestion_key()
    with database() as db:
        db.add(User(
            email=email.lower(),
            name=name,
            password_hash=None,
            oauth_provider=oauth_provider,
            api_key_hash=hash_ingestion_key(key),
            created_at=time.time(),
        ))


def register_or_login_oauth_user(email: str, name: str, provider: str) -> str:
    """Return a JWT for the user, creating the account if it doesn't exist."""
    email = email.lower()
    with database() as db:
        user = db.get(User, email)
    if not user:
        _create_oauth_user(email, name, provider)
    return create_access_token({"sub": email, "name": name})


def user_from_ingestion_key(key: str) -> dict:
    if not key or not key.startswith("ect_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid EcoTrace ingestion key is required",
        )
    with database() as db:
        from sqlalchemy import select
        user = db.scalar(select(User).where(User.api_key_hash == hash_ingestion_key(key)))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid EcoTrace ingestion key",
        )
    return {"email": user.email, "name": user.name}
