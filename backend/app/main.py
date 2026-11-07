import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routes.auth import router as auth_router
from .routes.analysis import router as analysis_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AI TrustShield API", version="1.1.0", description="AI-assisted document screening API. Screening is not proof of authenticity.")
_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [x.strip().rstrip("/") for x in _origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(analysis_router)

@app.get("/")
def root():
    return {"name": "AI TrustShield API", "status": "running", "docs": "/docs"}

@app.get("/api/health")
def health():
    return {"status": "ok"}
