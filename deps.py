import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from db_manager import db
from security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


class CurrentContext(BaseModel):
    user_id: int
    username: str
    role: str
    company_id: int | None


def get_current_context(token: str = Depends(oauth2_scheme)) -> CurrentContext:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_error

    username = payload.get("sub")
    if username is None:
        raise credentials_error

    # Expects db.get_user_by_username(username) -> dict with
    # id, username, hashed_password, role, company_id (or None).
    user = db.get_user_by_username(username)
    if user is None:
        raise credentials_error

    return CurrentContext(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        company_id=user["company_id"],
    )


def require_admin(context: CurrentContext = Depends(get_current_context)) -> CurrentContext:
    if context.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return context
