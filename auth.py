from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pwdlib import PasswordHash

SECRET_KEY, ALGORITHM = "change-this-later", "HS256"
pwd = PasswordHash.recommended()
security = HTTPBearer()

# Password helpers
hash_password = pwd.hash
verify_password = pwd.verify


# Token creation
def create_token(user_id: int) -> str:
  payload = {
      "user_id": user_id,
      "exp": datetime.now(timezone.utc) + timedelta(hours=24),
  }
  return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Auth dependency
def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(security),
) -> int:
  try:
    payload = jwt.decode(cred.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    if user_id := payload.get("user_id"):
      return user_id
  except Exception:
    pass
  raise HTTPException(status_code=401, detail="Invalid or expired token")
