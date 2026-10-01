import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

print("SECRET KEY LOADED:", bool(SECRET_KEY)) 


pwd = PasswordHash((BcryptHasher(),))
security = HTTPBearer()

hash_password = pwd.hash
verify_password = pwd.verify


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


def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    try:
        payload = jwt.decode(
            cred.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if user_id := payload.get("user_id"):
            return user_id

    except Exception:
        pass

    raise HTTPException(
        status_code=401,
        detail="Invalid or expired token"
    )