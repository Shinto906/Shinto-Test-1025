import io

import boto3
import yaml
from botocore.client import Config as BotoConfig
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _s3():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )


def _serialize(d: models.Document):
    return {
        "id": d.id,
        "tenant_id": d.tenant_id,
        "owner_id": d.owner_id,
        "title": d.title,
        "visibility": d.visibility,
        "s3_key": d.s3_key,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("")
def list_documents(
    db: Session = Depends(get_db), current: models.User = Depends(get_current_user)
):
    docs = (
        db.query(models.Document)
        .filter(models.Document.tenant_id == current.tenant_id)
        .order_by(models.Document.created_at.desc())
        .all()
    )
    return [_serialize(d) for d in docs]


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(doc)


@router.post("")
def create_document(
    title: str = Form(...),
    visibility: str = Form("private"),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    key = None
    if file is not None:
        key = f"{current.tenant_id}/{file.filename}"
        try:
            content = file.file.read()
            _s3().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=content)
        except Exception:
            key = f"local:{file.filename}"
    doc = models.Document(
        tenant_id=current.tenant_id,
        owner_id=current.id,
        title=title,
        visibility=visibility,
        s3_key=key,
    )
    db.add(doc)
    db.commit()
    return _serialize(doc)


@router.get("/{doc_id}/download")
def download_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc or not doc.s3_key:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        obj = _s3().get_object(Bucket=settings.S3_BUCKET, Key=doc.s3_key)
        data = obj["Body"].read()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Storage error: {exc}")
    return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")


@router.post("/import")
async def import_documents(
    body: dict = None,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    """Bulk-import documents from a YAML manifest.

    The manifest is a list of {title, visibility} entries."""
    raw = (body or {}).get("manifest", "")
    parsed = yaml.load(raw, Loader=yaml.Loader)
    created = []
    if isinstance(parsed, list):
        for entry in parsed:
            if not isinstance(entry, dict):
                continue
            doc = models.Document(
                tenant_id=current.tenant_id,
                owner_id=current.id,
                title=str(entry.get("title", "untitled")),
                visibility=str(entry.get("visibility", "private")),
            )
            db.add(doc)
            created.append(doc)
        db.commit()
    return {"imported": len(created)}
