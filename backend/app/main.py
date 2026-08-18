"""Rhadix CRM — FastAPI backend.
Stakeholder-/relatiebeheer rond RSO's en VVT-aanbieders, met krachtenveld-analyse.
Resource-server binnen het Rhadix-platform: accepteert het centrale SureSync ID-token
(RS256/JWKS) én een eigen lokale login (HS256) zodat de admin altijd kan inloggen.
"""
from __future__ import annotations

import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import init_db
from app.routers import health, meta, admin, org, crm, tasks
from app.auth.app_access import require_app_access
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


# Applicatietoegang via de centrale apps-claim (zie auth/app_access.py). Zonder
# token doet de dependency niets, zodat publieke routes ongewijzigd blijven.
# /api/auth blijft ongegate, zodat de frontend ook zonder toewijzing /auth/me kan
# ophalen en een verklarende melding kan tonen i.p.v. een blinde 401/403-lus.
_app_access = [Depends(require_app_access)]

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(meta.router, prefix="/api", tags=["meta"])
app.include_router(auth_router, prefix="/api/auth")
app.include_router(admin.router, prefix="/api/admin", dependencies=_app_access)
app.include_router(org.router, prefix="/api/org", dependencies=_app_access)
app.include_router(crm.router, prefix="/api/crm", dependencies=_app_access)
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"], dependencies=_app_access)


@app.get("/api")
def root():
    return {"app": "Rhadix CRM", "edition": "Stakeholder & Krachtenveld", "version": APP_VERSION}
