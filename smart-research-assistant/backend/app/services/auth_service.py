"""
Authentication service: user registration, login, JWT token management.
Uses a JSON file as the user store (swap to a real DB in production).
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.logging import logger
from app.models.schemas import RegisterRequest, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthService:
    def __init__(self):
        settings = get_settings()
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes
        self.users_path = Path(settings.users_db_path)
        self._ensure_users_file()

    def _ensure_users_file(self):
        self.users_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.users_path.exists():
            self.users_path.write_text("[]")

    def _load_users(self) -> list[dict]:
        return json.loads(self.users_path.read_text())

    def _save_users(self, users: list[dict]):
        self.users_path.write_text(json.dumps(users, indent=2))

    def _find_user(self, username: str) -> dict | None:
        users = self._load_users()
        for user in users:
            if user["username"] == username:
                return user
        return None

    def _find_user_by_email(self, email: str) -> dict | None:
        users = self._load_users()
        for user in users:
            if user["email"] == email:
                return user
        return None

    def register(self, request: RegisterRequest) -> UserResponse:
        """Register a new user."""
        if self._find_user(request.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken.",
            )
        if self._find_user_by_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

        user = {
            "id": uuid.uuid4().hex[:16],
            "username": request.username,
            "email": request.email,
            "full_name": request.full_name,
            "hashed_password": pwd_context.hash(request.password),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        users = self._load_users()
        users.append(user)
        self._save_users(users)

        logger.info(f"User registered: {request.username}")
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            created_at=user["created_at"],
        )

    def authenticate(self, username: str, password: str) -> dict:
        """Verify credentials and return user dict."""
        user = self._find_user(username)
        if not user or not pwd_context.verify(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )
        return user

    def create_token(self, user: dict) -> str:
        """Create a JWT access token for the user."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        payload = {
            "sub": user["username"],
            "uid": user["id"],
            "exp": expire,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        """Decode and validate a JWT token. Returns the payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token.",
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired or invalid.",
            )

    def get_user_from_token(self, token: str) -> UserResponse:
        """Get full user info from a token."""
        payload = self.verify_token(token)
        user = self._find_user(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            created_at=user["created_at"],
        )


# ── Singleton ────────────────────────────────────────────────────

_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# ── FastAPI dependency for protected routes ──────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserResponse:
    """Dependency that extracts and validates the user from the Authorization header."""
    auth = get_auth_service()
    return auth.get_user_from_token(credentials.credentials)
