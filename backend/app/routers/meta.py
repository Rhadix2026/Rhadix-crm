import os
from fastapi import APIRouter
router = APIRouter()

@router.get("/meta")
def meta():
    return {
        "name": "Rhadix CRM",
        "edition": "Stakeholder & Krachtenveld",
        "version": "0.1.0",
        "environment": os.getenv("RHADIX_ENV", "development"),
        "modules": [
            {"key": "relaties",    "label": "Relatiebeheer",    "status": "available"},
            {"key": "krachtenveld","label": "Krachtenveld",     "status": "available"},
            {"key": "opvolging",   "label": "Opvolging",        "status": "available"},
            {"key": "dashboard",   "label": "Rapportage",       "status": "available"},
        ],
    }
