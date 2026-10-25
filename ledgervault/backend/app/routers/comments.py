from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/documents", tags=["comments"])


def _serialize(c: models.Comment):
    return {
        "id": c.id,
        "document_id": c.document_id,
        "author_id": c.author_id,
        "body": c.body,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/{doc_id}/comments")
def list_comments(
    doc_id: str,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    comments = (
        db.query(models.Comment)
        .filter(models.Comment.document_id == doc_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )
    return [_serialize(c) for c in comments]


@router.post("/{doc_id}/comments")
def add_comment(
    doc_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    body = payload.get("body", "")
    comment = models.Comment(document_id=doc_id, author_id=current.id, body=body)
    db.add(comment)
    db.commit()
    return _serialize(comment)
