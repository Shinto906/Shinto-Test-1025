import hashlib
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..security import create_token, hash_password, verify_password
from .. import models

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


class RegisterIn(BaseModel):
    tenant_id: str
    email: str
    password: str
    full_name: str | None = None


class ForgotIn(BaseModel):
    email: str


class ResetIn(BaseModel):
    token: str
    new_password: str


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(
        {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "email": user.email,
        }
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    tenant = db.query(models.Tenant).filter(models.Tenant.id == body.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = models.User(
        tenant_id=body.tenant_id,
        email=body.email,
        full_name=body.full_name or body.email.split("@")[0],
        password_hash=hash_password(body.password),
        role="member",
    )
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email}


@router.post("/forgot-password")
def forgot_password(body: ForgotIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if user:
        day = datetime.utcnow().strftime("%Y-%m-%d")
        token = hashlib.md5(f"{user.email}:{day}".encode()).hexdigest()[:12]
        pr = models.PasswordReset(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(pr)
        db.commit()
    return {"status": "If the account exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(body: ResetIn, db: Session = Depends(get_db)):
    pr = (
        db.query(models.PasswordReset)
        .filter(
            models.PasswordReset.token == body.token,
            models.PasswordReset.used == False,  # noqa: E712
        )
        .first()
    )
    if not pr or (pr.expires_at and pr.expires_at < datetime.utcnow()):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(models.User).filter(models.User.id == pr.user_id).first()
    user.password_hash = hash_password(body.new_password)
    pr.used = True
    db.commit()
    return {"status": "Password updated"}
