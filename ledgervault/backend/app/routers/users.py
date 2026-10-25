from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search")
def search_users(
    q: str = "",
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    query = db.query(models.User).filter(models.User.tenant_id == current.tenant_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(models.User.email.ilike(like), models.User.full_name.ilike(like))
        )
    results = query.limit(50).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "tenant_id": u.tenant_id,
        }
        for u in results
    ]
