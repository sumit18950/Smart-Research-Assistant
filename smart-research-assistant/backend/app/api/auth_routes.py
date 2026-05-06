"""
Authentication API routes: register, login, and current user.
"""

from fastapi import APIRouter, Depends
from app.models.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    ErrorResponse,
)
from app.services.auth_service import get_auth_service, get_current_user

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    responses={409: {"model": ErrorResponse}},
)
async def register(request: RegisterRequest):
    """Register a new user account."""
    auth = get_auth_service()
    return auth.register(request)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(request: LoginRequest):
    """Authenticate and receive a JWT access token."""
    auth = get_auth_service()
    user = auth.authenticate(request.username, request.password)
    token = auth.create_token(user)
    return TokenResponse(access_token=token)


@auth_router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}},
)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user
