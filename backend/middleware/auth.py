"""Authentication middleware for JWT token validation."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Optional

import bcrypt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

if not hasattr(bcrypt, "__about__"):
    setattr(bcrypt, "__about__", SimpleNamespace(__version__=bcrypt.__version__))

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "nagare-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns the payload dict."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        return {"id": user_id, "username": username}
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency that extracts the current user from the JWT token.
    
    Returns a dict with 'id' and 'username' keys.
    Raises 401 if token is missing or invalid.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(token)


async def get_current_user_from_cookie(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
) -> dict:
    cookie_token = request.cookies.get("access_token")
    auth_token = cookie_token or token
    if auth_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(auth_token)


async def validate_csrf_token(
    request: Request,
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"} or not request.url.path.startswith("/api/"):
        return

    csrf_token = request.cookies.get("csrf_token")
    if x_csrf_token is None or csrf_token is None or x_csrf_token != csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
