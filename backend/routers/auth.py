"""Authentication routes — register, login, me."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status

from models.user import UserCreate, UserLogin, UserResponse, Token
from services.user_manager import UserManager
from middleware.auth import create_access_token, get_current_user_from_cookie, validate_csrf_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
user_manager = UserManager()
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24


def set_auth_cookies(response: Response, access_token: str) -> None:
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="strict",
        path="/",
        max_age=COOKIE_MAX_AGE_SECONDS,
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=False,
        samesite="strict",
        path="/",
        max_age=COOKIE_MAX_AGE_SECONDS,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, response: Response):
    """Register a new user and return a JWT token."""
    if user_manager.user_exists(username=user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    try:
        created = user_manager.create_user(
            username=user.username,
            password=user.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # Create token
    token = create_access_token(data={"sub": created["id"], "username": created["username"]})
    set_auth_cookies(response, token)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, response: Response):
    """Authenticate a user and return a JWT token."""
    user = user_manager.authenticate_user(
        username=credentials.username,
        password=credentials.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(data={"sub": user["id"], "username": user["username"]})
    set_auth_cookies(response, token)
    return Token(access_token=token)


@router.post("/logout", response_model=dict[str, str], dependencies=[Depends(validate_csrf_token)])
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="csrf_token", path="/")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user_from_cookie)):
    """Get the current authenticated user's profile."""
    user = user_manager.get_user(current_user["id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
