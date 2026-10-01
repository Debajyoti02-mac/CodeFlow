import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher


# Load environment variables from .env locally
# Render will use its own environment variables.
load_dotenv()


# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

print("SECRET KEY LOADED:", bool(SECRET_KEY))


# Password hashing
pwd = PasswordHash((BcryptHasher(),))

hash_password = pwd.hash
verify_password = pwd.verify


# HTTP Bearer authentication
# auto_error=False lets us detect a missing Authorization header ourselves.
security = HTTPBearer(auto_error=False)


# ============================================================
# Token creation
# ============================================================

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ============================================================
# Auth dependency
# ============================================================

def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(security),
) -> int:

    # No Authorization header
    if cred is None:
        print("NO AUTHORIZATION HEADER")

        raise HTTPException(
            status_code=401,
            detail="No authorization token"
        )

    try:
        # Don't print the complete token.
        print("TOKEN RECEIVED:", cred.credentials[:20])

        payload = jwt.decode(
            cred.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        print("PAYLOAD:", payload)

        user_id = payload.get("user_id")

        if user_id:
            return user_id

    except Exception as e:
        print("JWT ERROR:", repr(e))

    raise HTTPException(
        status_code=401,
        detail="Invalid or expired token"
    )