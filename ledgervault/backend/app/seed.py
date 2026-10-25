from decimal import Decimal

import boto3
from botocore.client import Config as BotoConfig
from sqlalchemy.orm import Session

from .config import settings
from .security import hash_password
from . import models


def _ensure_bucket_and_sample():
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=BotoConfig(signature_version="s3v4"),
        )
        existing = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
        if settings.S3_BUCKET not in existing:
            s3.create_bucket(Bucket=settings.S3_BUCKET)
    except Exception:
        pass


def run_seed(db: Session):
    if db.query(models.User).count() > 0:
        return

    _ensure_bucket_and_sample()

    aozora = models.Tenant(name="Aozora Corp", plan="enterprise")
    beacon = models.Tenant(name="Beacon Inc", plan="standard")
    db.add_all([aozora, beacon])
    db.flush()

    pw = hash_password("Password123!")

    alice = models.User(
        tenant_id=aozora.id, email="alice@aozora.example",
        full_name="Alice Member", password_hash=pw, role="member",
    )
    mallory = models.User(
        tenant_id=aozora.id, email="mallory@aozora.example",
        full_name="Mallory Member", password_hash=pw, role="member",
    )
    amanda = models.User(
        tenant_id=aozora.id, email="manager@aozora.example",
        full_name="Amanda Manager", password_hash=pw, role="manager",
    )
    adam = models.User(
        tenant_id=aozora.id, email="admin@aozora.example",
        full_name="Adam Admin", password_hash=pw, role="admin",
    )
    bob = models.User(
        tenant_id=beacon.id, email="bob@beacon.example",
        full_name="Bob Beacon", password_hash=pw, role="member",
    )
    root = models.User(
        tenant_id=beacon.id, email="root@system.example",
        full_name="System Root", password_hash=pw, role="admin",
        is_super_admin=True,
    )
    db.add_all([alice, mallory, amanda, adam, bob, root])
    db.flush()

    beacon_secret = models.Document(
        tenant_id=beacon.id, owner_id=bob.id,
        title="Beacon Inc - Q3 Financials (confidential)",
        visibility="private", s3_key=None,
    )
    aozora_doc = models.Document(
        tenant_id=aozora.id, owner_id=alice.id,
        title="Aozora onboarding notes", visibility="tenant", s3_key=None,
    )
    db.add_all([beacon_secret, aozora_doc])
    db.flush()

    db.add(models.Comment(
        document_id=aozora_doc.id, author_id=alice.id,
        body="Welcome to the team!",
    ))

    db.add(models.Expense(
        tenant_id=aozora.id, user_id=alice.id, amount=Decimal("12000"),
        currency="JPY", category="travel", description="Client visit",
        status="submitted",
    ))
    db.add(models.SavedFilter(
        tenant_id=aozora.id, user_id=alice.id, name="Approved only",
        expression="status = 'approved'",
    ))
    db.commit()
