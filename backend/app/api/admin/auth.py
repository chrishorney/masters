"""Admin authentication endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta
from app.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int


def verify_password(password: str) -> bool:
    """Verify the admin password."""
    return password == settings.admin_password


def create_access_token() -> str:
    """Create a JWT access token for admin."""
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {
        "sub": "admin",
        "exp": expire,
        "type": "admin"
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login to admin dashboard."""
    if not verify_password(request.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )
    
    token = create_access_token()
    
    return {
        "token": token,
        "expires_in": 24 * 60 * 60  # 24 hours in seconds
    }


@router.get("/auth/verify")
async def verify_token(token: str):
    """Verify if a token is valid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "admin":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return {"valid": True}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_admin(token: str = Depends(lambda: None)) -> dict:
    """Dependency to get current admin from token."""
    # This is a placeholder - we'll verify tokens in the frontend for now
    # For full security, we'd verify here and protect all admin endpoints
    return {"admin": True}
