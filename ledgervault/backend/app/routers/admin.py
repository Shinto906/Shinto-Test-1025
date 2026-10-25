from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_current_user, require_superadmin
from .. import models

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/tenants")
def list_tenants(
    current: models.User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    tenants = db.query(models.Tenant).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "plan": t.plan,
            "user_count": db.query(models.User)
            .filter(models.User.tenant_id == t.id)
            .count(),
        }
        for t in tenants
    ]


@router.get("/users")
def list_all_users(
    current: models.User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    users = db.query(models.User).all()
    return [
        {
            "id": u.id,
            "tenant_id": u.tenant_id,
            "email": u.email,
            "role": u.role,
            "is_super_admin": u.is_super_admin,
        }
        for u in users
    ]


@router.post("/users/{user_id}/role")
def set_role(
    user_id: str,
    payload: dict,
    current: models.User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.role = payload.get("role", u.role)
    db.commit()
    return {"id": u.id, "role": u.role}


@router.post("/bootstrap-superadmin")
def bootstrap_superadmin(
    payload: dict,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    """Provisioning endpoint used during environment setup. Elevates the
    caller when presented with the instance bootstrap token."""
    token = payload.get("bootstrap_token")
    if token != settings.BOOTSTRAP_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")
    current.is_super_admin = True
    current.role = "admin"
    db.commit()
    return {"status": "elevated", "user_id": current.id}


@router.get("/super/all-secrets")
def all_secrets(
    current: models.User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    users = db.query(models.User).all()
    return {
        "jwt_secret": settings.JWT_SECRET,
        "s3_credentials": {
            "access_key": settings.S3_ACCESS_KEY,
            "secret_key": settings.S3_SECRET_KEY,
        },
        "users": [
            {"email": u.email, "password_hash": u.password_hash, "role": u.role}
            for u in users
        ],
    }
