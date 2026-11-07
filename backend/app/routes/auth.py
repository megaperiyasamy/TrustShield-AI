import hashlib
import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, PasswordResetToken
from ..schemas import RegisterRequest, LoginRequest, PasswordResetRequest, PasswordResetConfirm
from ..auth import hash_password, verify_password, create_token, get_current_user
from ..services.emailer import send_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

def user_dict(u):
    return {"id": u.id, "name": u.name, "email": u.email}

def normalize_email(email: str) -> str:
    return email.strip().lower()

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    name = req.name.strip()
    email = normalize_email(str(req.email))
    if not name:
        raise HTTPException(400, "Please enter your name")
    if len(name) > 120:
        raise HTTPException(400, "Name must be 120 characters or fewer")
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters long")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists. Please log in instead.")
    u = User(name=name, email=email, password_hash=hash_password(req.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"access_token": create_token(u), "token_type": "bearer", "user": user_dict(u)}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = normalize_email(str(req.email))
    u = db.query(User).filter(User.email == email).first()
    if not u or not verify_password(req.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password. If this is your first time, create an account first.")
    return {"access_token": create_token(u), "token_type": "bearer", "user": user_dict(u)}

@router.get("/me")
def me(user=Depends(get_current_user)):
    return user_dict(user)

@router.post("/forgot-password")
def forgot_password(req: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    email = normalize_email(str(req.email))
    user = db.query(User).filter(User.email == email).first()
    response = {"message": "If an account exists for that email, password reset instructions have been prepared."}
    if not user:
        return response

    now = datetime.utcnow()
    # Invalidate unused previous reset links for this account.
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).update({"used_at": now})
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    record = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=now + timedelta(minutes=30))
    db.add(record)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url.rstrip('/')}/reset-password?token={quote(raw_token)}"
    try:
        sent = send_email(user.email, "Reset your AI TrustShield password", f"Hello {user.name},\n\nUse this link to reset your AI TrustShield password. It expires in 30 minutes and can only be used once:\n\n{reset_url}\n\nIf you did not request this, you can ignore this email.")
    except Exception:
        # Do not leak account state or SMTP details to the caller.
        sent = False
    if not sent and os.getenv("ENVIRONMENT", "development").lower() != "production":
        response["development_reset_url"] = reset_url
    return response

@router.post("/reset-password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters long")
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    now = datetime.utcnow()
    if not record or record.used_at is not None or record.expires_at < now:
        raise HTTPException(400, "This password reset link is invalid or expired. Request a new one.")
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(400, "This password reset link is invalid or expired. Request a new one.")
    user.password_hash = hash_password(req.password)
    record.used_at = now
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).update({"used_at": now})
    db.commit()
    return {"message": "Password updated successfully. Please log in with your new password."}
