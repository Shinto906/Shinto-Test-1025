from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .security import decode_token
from . import models


def get_claims(authorization: str = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return claims


def get_current_user(
    claims: dict = Depends(get_claims), db: Session = Depends(get_db)
) -> models.User:
    user = db.query(models.User).filter(models.User.id == claims.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unknown subject")
    return user


def require_superadmin(
    current: models.User = Depends(get_current_user),
) -> models.User:
    if not current.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin required")
    return current
