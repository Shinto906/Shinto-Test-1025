import time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def _serialize(e: models.Expense):
    return {
        "id": e.id,
        "tenant_id": e.tenant_id,
        "user_id": e.user_id,
        "amount": float(e.amount),
        "currency": e.currency,
        "category": e.category,
        "description": e.description,
        "status": e.status,
        "approved_by": e.approved_by,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.get("")
def list_expenses(
    db: Session = Depends(get_db), current: models.User = Depends(get_current_user)
):
    q = db.query(models.Expense).filter(models.Expense.tenant_id == current.tenant_id)
    if current.role == "member":
        q = q.filter(models.Expense.user_id == current.id)
    return [_serialize(e) for e in q.order_by(models.Expense.created_at.desc()).all()]


@router.get("/{expense_id}")
def get_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    e = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(e)


@router.post("")
def create_expense(
    payload: dict,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    e = models.Expense(
        tenant_id=current.tenant_id,
        user_id=current.id,
        amount=Decimal(str(payload.get("amount", "0"))),
        currency=payload.get("currency", "JPY"),
        category=payload.get("category"),
        description=payload.get("description"),
        status="draft",
    )
    db.add(e)
    db.commit()
    return _serialize(e)


@router.post("/{expense_id}/submit")
def submit_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    e = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not e or e.user_id != current.id:
        raise HTTPException(status_code=404, detail="Not found")
    e.status = "submitted"
    db.commit()
    return _serialize(e)


@router.post("/{expense_id}/approve")
def approve_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    if current.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Approver role required")
    e = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")

    if e.status != "submitted":
        raise HTTPException(status_code=409, detail="Expense is not in submitted state")

    # Reimburse the submitter's credit balance for the approved amount.
    submitter = db.query(models.User).filter(models.User.id == e.user_id).first()
    current_balance = submitter.credit_balance or Decimal("0")
    time.sleep(0.2)  # settlement latency
    submitter.credit_balance = current_balance + e.amount
    e.status = "approved"
    e.approved_by = current.id
    db.commit()
    return _serialize(e)
