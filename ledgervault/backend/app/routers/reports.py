from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/reports", tags=["reports"])


class _SaveError(Exception):
    pass


def _validate_expression(expr: str):
    # Basic guard against stacked statements.
    if ";" in expr:
        raise _SaveError("Multiple statements are not allowed")
    if len(expr) > 500:
        raise _SaveError("Expression too long")


@router.post("/filters")
def save_filter(
    payload: dict,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    expr = payload.get("expression", "")
    name = payload.get("name", "filter")
    try:
        _validate_expression(expr)
    except _SaveError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    f = models.SavedFilter(
        tenant_id=current.tenant_id,
        user_id=current.id,
        name=name,
        expression=expr,
    )
    db.add(f)
    db.commit()
    return {"id": f.id, "name": f.name}


@router.get("/filters")
def list_filters(
    db: Session = Depends(get_db), current: models.User = Depends(get_current_user)
):
    fs = (
        db.query(models.SavedFilter)
        .filter(models.SavedFilter.tenant_id == current.tenant_id)
        .all()
    )
    return [{"id": f.id, "name": f.name, "expression": f.expression} for f in fs]


@router.post("/run")
def run_report(
    payload: dict,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    filter_id = payload.get("filter_id")
    f = db.query(models.SavedFilter).filter(models.SavedFilter.id == filter_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Filter not found")

    sql = (
        "SELECT id, amount, status, category FROM expenses "
        f"WHERE tenant_id = '{current.tenant_id}' AND ({f.expression})"
    )
    try:
        rows = db.execute(text(sql)).fetchall()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Report failed: {exc}")
    return {"sql": sql, "rows": [list(r) for r in rows]}
