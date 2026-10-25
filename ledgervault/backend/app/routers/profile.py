import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/profile", tags=["profile"])

_EDITABLE = {"full_name", "avatar_url"}


def _serialize(u: models.User):
    return {
        "id": u.id,
        "tenant_id": u.tenant_id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "is_super_admin": u.is_super_admin,
        "credit_balance": float(u.credit_balance or 0),
        "avatar_url": u.avatar_url,
    }


@router.get("/me")
def get_me(current: models.User = Depends(get_current_user)):
    return _serialize(current)


@router.patch("/me")
def update_me(
    payload: dict,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    for key, value in payload.items():
        if key in _EDITABLE:
            setattr(current, key, value)
    db.commit()
    return _serialize(current)


@router.post("/me/avatar-from-url")
def avatar_from_url(
    payload: dict,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    try:
        resp = requests.get(url, timeout=5)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {exc}")
    current.avatar_url = url
    db.commit()
    return {
        "status": "ok",
        "fetched_bytes": len(resp.content),
        "content_type": resp.headers.get("Content-Type"),
        "preview": resp.text[:500],
    }
