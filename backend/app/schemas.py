from pydantic import BaseModel, EmailStr
from typing import List, Optional

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Finding(BaseModel):
    severity: str
    title: str
    detail: str
    evidence: str = ""

class AnalysisResponse(BaseModel):
    id: int
    filename: str
    document_type: str
    score: int
    risk_level: str
    confidence: int
    issues_count: int
    findings: List[Finding]
    recommendations: List[str]
    extracted_text: str
    created_at: str
    report_url: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    password: str
