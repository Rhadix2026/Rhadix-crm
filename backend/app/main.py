"""Rhadix CRM — FastAPI backend.
Stakeholder-/relatiebeheer rond RSO's en VVT-aanbieders, met krachtenveld-analyse.
Resource-server binnen het Rhadix-platform: accepteert het centrale SureSync ID-token
(RS256/JWKS) én een eigen lokale login (HS256) zodat de admin altijd kan inloggen.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import init_db
from app.routers import health, meta, admin, org, crm
from app.auth.router import router as auth_router

APP_VERSION = "0.1.0"

app = FastAPI(title="Rhadix CRM API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(meta.router, prefix="/api", tags=["meta"])
app.include_router(auth_router, prefix="/api/auth")
app.include_router(admin.router, prefix="/api/admin")
app.include_router(org.router, prefix="/api/org")
app.include_router(crm.router, prefix="/api/crm")


@app.get("/api")
def root():
    return {"app": "Rhadix CRM", "edition": "Stakeholder & Krachtenveld", "version": APP_VERSION}
