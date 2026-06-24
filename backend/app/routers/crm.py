"""crm.py — CRM-kern: organisaties, contactpersonen, krachtenveld, stakeholders,
activiteiten en rapportage. Alles tenant-gescoped."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.services.krachtenveld_generator import genereer_krachtenveld
from app.database import get_db
from app.models.auth_models import User
from app.models.crm_models import (Activiteit, Contactpersoon, Krachtenveld,
                                    Organisatie, Stakeholder)

router = APIRouter(tags=["crm"])


def _uuid(val: str, label="ID") -> uuid.UUID:
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        raise HTTPException(400, f"Ongeldig {label}: {val!r}")


def _quadrant(invloed: Optional[str], betrokkenheid: Optional[str]) -> str:
    """Kwadrant uit de matrix invloed (y) x betrokkenheid (x)."""
    hoog_inv = (invloed or "").lower() in ("hoog",)
    hoog_bet = (betrokkenheid or "").lower() in ("hoog",)
    if hoog_inv and hoog_bet:   return "Actief betrekken"
    if hoog_inv and not hoog_bet: return "Tevreden houden"
    if not hoog_inv and hoog_bet: return "Mee nemen"
    return "Informeren"


# ── serialisatie ──────────────────────────────────────────────────────────────
def _org(o: Organisatie) -> dict:
    return {
        "id": str(o.id), "soort": o.soort, "naam": o.naam, "type": o.type,
        "werkgebied": o.werkgebied, "cluster": o.cluster, "provincies": o.provincies,
        "website": o.website, "bron_url": o.bron_url, "bron_opmerking": o.bron_opmerking,
        "aantal_aangesloten": o.aantal_aangesloten, "focus_themas": o.focus_themas,
        "rso_naam": o.rso_naam, "betrouwbaarheid": o.betrouwbaarheid,
        "onderbouwing": o.onderbouwing, "actie_validatie": o.actie_validatie,
        "aantal_contacten": len(o.contactpersonen), "aantal_krachtenvelden": len(o.krachtenvelden),
    }


def _cp(c: Contactpersoon) -> dict:
    return {
        "id": str(c.id), "organisatie_id": str(c.organisatie_id) if c.organisatie_id else None,
        "categorie": c.categorie, "organisatie_naam": c.organisatie_naam, "rso_regio": c.rso_regio,
        "rolniveau": c.rolniveau, "naam": c.naam, "functie": c.functie, "email": c.email,
        "telefoon": c.telefoon, "bron_url": c.bron_url, "bron_type": c.bron_type,
        "zekerheid": c.zekerheid, "opmerking": c.opmerking,
    }


def _sh(s: Stakeholder) -> dict:
    return {
        "id": str(s.id), "krachtenveld_id": str(s.krachtenveld_id), "naam": s.naam, "rol": s.rol,
        "verantwoordelijkheden": s.verantwoordelijkheden, "doelen_belangen": s.doelen_belangen,
        "invloed": s.invloed, "betrokkenheid": s.betrokkenheid, "houding": s.houding,
        "argumenten": s.argumenten, "belemmeringen": s.belemmeringen, "aanpak": s.aanpak,
        "laatste_contact": s.laatste_contact, "volgende_stap": s.volgende_stap,
        "kwadrant": _quadrant(s.invloed, s.betrokkenheid),
    }


def _kv(k: Krachtenveld, with_sh=False) -> dict:
    d = {
        "id": str(k.id), "organisatie_id": str(k.organisatie_id) if k.organisatie_id else None,
        "titel": k.titel, "regio": k.regio, "bestuurlijk_orgaan": k.bestuurlijk_orgaan,
        "operationeel_orgaan": k.operationeel_orgaan, "besluitvormingsproces": k.besluitvormingsproces,
        "beslissingsfrequentie": k.beslissingsfrequentie, "kernopgave": k.kernopgave,
        "beslissingsdrivers": k.beslissingsdrivers, "belemmeringen": k.belemmeringen,
        "kansen": k.kansen, "waarde": k.waarde, "volgende_stappen": k.volgende_stappen,
        "notities": k.notities, "eigenaar": k.eigenaar,
        "aantal_stakeholders": len(k.stakeholders),
    }
    if with_sh:
        d["stakeholders"] = [_sh(s) for s in k.stakeholders]
    return d


def _act(a: Activiteit) -> dict:
    return {
        "id": str(a.id), "organisatie_id": str(a.organisatie_id) if a.organisatie_id else None,
        "contactpersoon_id": str(a.contactpersoon_id) if a.contactpersoon_id else None,
        "krachtenveld_id": str(a.krachtenveld_id) if a.krachtenveld_id else None,
        "titel": a.titel, "soort": a.soort, "omschrijving": a.omschrijving,
        "status": a.status, "datum": a.datum.isoformat() if a.datum else None, "eigenaar": a.eigenaar,
    }


# ── ORGANISATIES ───────────────────────────────────────────────────────────────
class OrgBody(BaseModel):
    soort: str = "VVT"
    naam: str
    type: Optional[str] = None
    werkgebied: Optional[str] = None
    cluster: Optional[str] = None
    provincies: Optional[str] = None
    website: Optional[str] = None
    bron_url: Optional[str] = None
    bron_opmerking: Optional[str] = None
    aantal_aangesloten: Optional[int] = None
    focus_themas: Optional[str] = None
    rso_naam: Optional[str] = None
    betrouwbaarheid: Optional[str] = None
    onderbouwing: Optional[str] = None
    actie_validatie: Optional[str] = None


@router.get("/organisaties")
def list_orgs(soort: Optional[str] = None, rso: Optional[str] = None,
              q: Optional[str] = Query(None), db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    qry = db.query(Organisatie).filter(Organisatie.tenant_id == user.tenant_id)
    if soort: qry = qry.filter(Organisatie.soort == soort)
    if rso:   qry = qry.filter(Organisatie.rso_naam == rso)
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(Organisatie.naam.ilike(like), Organisatie.werkgebied.ilike(like),
                             Organisatie.provincies.ilike(like)))
    return [_org(o) for o in qry.order_by(Organisatie.soort, Organisatie.naam).all()]


@router.post("/organisaties", status_code=201)
def create_org(body: OrgBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = Organisatie(tenant_id=user.tenant_id, **body.model_dump())
    db.add(o); db.commit(); db.refresh(o)
    return _org(o)


def _get_org(org_id: str, db: Session, user: User) -> Organisatie:
    o = db.query(Organisatie).filter(Organisatie.id == _uuid(org_id),
                                     Organisatie.tenant_id == user.tenant_id).first()
    if not o:
        raise HTTPException(404, "Organisatie niet gevonden")
    return o


@router.get("/organisaties/{org_id}")
def get_org(org_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = _get_org(org_id, db, user)
    d = _org(o)
    d["contactpersonen"] = [_cp(c) for c in o.contactpersonen]
    d["krachtenvelden"]  = [_kv(k) for k in o.krachtenvelden]
    return d


@router.patch("/organisaties/{org_id}")
def update_org(org_id: str, body: OrgBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = _get_org(org_id, db, user)
    for k, v in body.model_dump().items():
        setattr(o, k, v)
    db.commit(); db.refresh(o)
    return _org(o)


@router.delete("/organisaties/{org_id}", status_code=204)
def delete_org(org_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = _get_org(org_id, db, user)
    db.delete(o); db.commit()


# ── CONTACTPERSONEN ─────────────────────────────────────────────────────────────
class CpBody(BaseModel):
    organisatie_id: Optional[str] = None
    categorie: Optional[str] = None
    organisatie_naam: Optional[str] = None
    rso_regio: Optional[str] = None
    rolniveau: Optional[str] = None
    naam: Optional[str] = None
    functie: Optional[str] = None
    email: Optional[str] = None
    telefoon: Optional[str] = None
    bron_url: Optional[str] = None
    bron_type: Optional[str] = None
    zekerheid: Optional[str] = None
    opmerking: Optional[str] = None


@router.get("/contactpersonen")
def list_cps(organisatie_id: Optional[str] = None, q: Optional[str] = None,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    qry = db.query(Contactpersoon).filter(Contactpersoon.tenant_id == user.tenant_id)
    if organisatie_id:
        qry = qry.filter(Contactpersoon.organisatie_id == _uuid(organisatie_id))
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(Contactpersoon.naam.ilike(like), Contactpersoon.organisatie_naam.ilike(like),
                             Contactpersoon.functie.ilike(like)))
    return [_cp(c) for c in qry.order_by(Contactpersoon.organisatie_naam, Contactpersoon.naam).all()]


@router.post("/contactpersonen", status_code=201)
def create_cp(body: CpBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = body.model_dump()
    if data.get("organisatie_id"):
        data["organisatie_id"] = _uuid(data["organisatie_id"])
    c = Contactpersoon(tenant_id=user.tenant_id, **data)
    db.add(c); db.commit(); db.refresh(c)
    return _cp(c)


@router.patch("/contactpersonen/{cp_id}")
def update_cp(cp_id: str, body: CpBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Contactpersoon).filter(Contactpersoon.id == _uuid(cp_id),
                                        Contactpersoon.tenant_id == user.tenant_id).first()
    if not c:
        raise HTTPException(404, "Contactpersoon niet gevonden")
    data = body.model_dump()
    if data.get("organisatie_id"):
        data["organisatie_id"] = _uuid(data["organisatie_id"])
    for k, v in data.items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return _cp(c)


@router.delete("/contactpersonen/{cp_id}", status_code=204)
def delete_cp(cp_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Contactpersoon).filter(Contactpersoon.id == _uuid(cp_id),
                                        Contactpersoon.tenant_id == user.tenant_id).first()
    if not c:
        raise HTTPException(404, "Contactpersoon niet gevonden")
    db.delete(c); db.commit()


# ── KRACHTENVELD ────────────────────────────────────────────────────────────────
class KvBody(BaseModel):
    organisatie_id: Optional[str] = None
    titel: str
    regio: Optional[str] = None
    bestuurlijk_orgaan: Optional[str] = None
    operationeel_orgaan: Optional[str] = None
    besluitvormingsproces: Optional[str] = None
    beslissingsfrequentie: Optional[str] = None
    kernopgave: Optional[str] = None
    beslissingsdrivers: Optional[str] = None
    belemmeringen: Optional[str] = None
    kansen: Optional[str] = None
    waarde: Optional[str] = None
    volgende_stappen: Optional[str] = None
    notities: Optional[str] = None
    eigenaar: Optional[str] = None


@router.get("/krachtenvelden")
def list_kv(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Krachtenveld).filter(Krachtenveld.tenant_id == user.tenant_id)\
             .order_by(Krachtenveld.titel).all()
    return [_kv(k) for k in rows]


@router.post("/krachtenvelden", status_code=201)
def create_kv(body: KvBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = body.model_dump()
    if data.get("organisatie_id"):
        data["organisatie_id"] = _uuid(data["organisatie_id"])
    k = Krachtenveld(tenant_id=user.tenant_id, **data)
    db.add(k); db.commit(); db.refresh(k)
    return _kv(k, with_sh=True)


@router.post("/organisaties/{org_id}/genereer-krachtenveld", status_code=201)
def genereer_kv(org_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Bouw automatisch een krachtenveld voor de organisatie: standaard RSO-rollen
    + de gekoppelde contactpersonen als stakeholders, met voorgevulde canvas-tekst."""
    org = _get_org(org_id, db, user)
    kv = genereer_krachtenveld(db, user.tenant_id, org)
    return _kv(kv, with_sh=True)


def _get_kv(kv_id: str, db: Session, user: User) -> Krachtenveld:
    k = db.query(Krachtenveld).filter(Krachtenveld.id == _uuid(kv_id),
                                      Krachtenveld.tenant_id == user.tenant_id).first()
    if not k:
        raise HTTPException(404, "Krachtenveld niet gevonden")
    return k


@router.get("/krachtenvelden/{kv_id}")
def get_kv(kv_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _kv(_get_kv(kv_id, db, user), with_sh=True)


@router.patch("/krachtenvelden/{kv_id}")
def update_kv(kv_id: str, body: KvBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    k = _get_kv(kv_id, db, user)
    data = body.model_dump()
    if data.get("organisatie_id"):
        data["organisatie_id"] = _uuid(data["organisatie_id"])
    for key, v in data.items():
        setattr(k, key, v)
    db.commit(); db.refresh(k)
    return _kv(k, with_sh=True)


@router.delete("/krachtenvelden/{kv_id}", status_code=204)
def delete_kv(kv_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    k = _get_kv(kv_id, db, user)
    db.delete(k); db.commit()


# ── STAKEHOLDERS ────────────────────────────────────────────────────────────────
class ShBody(BaseModel):
    naam: str
    rol: Optional[str] = None
    verantwoordelijkheden: Optional[str] = None
    doelen_belangen: Optional[str] = None
    invloed: Optional[str] = "Middel"
    betrokkenheid: Optional[str] = "Middel"
    houding: Optional[str] = "Onbekend"
    argumenten: Optional[str] = None
    belemmeringen: Optional[str] = None
    aanpak: Optional[str] = None
    laatste_contact: Optional[str] = None
    volgende_stap: Optional[str] = None


@router.post("/krachtenvelden/{kv_id}/stakeholders", status_code=201)
def add_sh(kv_id: str, body: ShBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    k = _get_kv(kv_id, db, user)
    s = Stakeholder(tenant_id=user.tenant_id, krachtenveld_id=k.id, **body.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return _sh(s)


@router.patch("/stakeholders/{sh_id}")
def update_sh(sh_id: str, body: ShBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Stakeholder).filter(Stakeholder.id == _uuid(sh_id),
                                     Stakeholder.tenant_id == user.tenant_id).first()
    if not s:
        raise HTTPException(404, "Stakeholder niet gevonden")
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return _sh(s)


@router.delete("/stakeholders/{sh_id}", status_code=204)
def delete_sh(sh_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Stakeholder).filter(Stakeholder.id == _uuid(sh_id),
                                     Stakeholder.tenant_id == user.tenant_id).first()
    if not s:
        raise HTTPException(404, "Stakeholder niet gevonden")
    db.delete(s); db.commit()


# ── ACTIVITEITEN (opvolging) ─────────────────────────────────────────────────────
class ActBody(BaseModel):
    organisatie_id: Optional[str] = None
    contactpersoon_id: Optional[str] = None
    krachtenveld_id: Optional[str] = None
    titel: str
    soort: str = "taak"
    omschrijving: Optional[str] = None
    status: str = "open"
    datum: Optional[date] = None
    eigenaar: Optional[str] = None


@router.get("/activiteiten")
def list_act(status: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    qry = db.query(Activiteit).filter(Activiteit.tenant_id == user.tenant_id)
    if status:
        qry = qry.filter(Activiteit.status == status)
    return [_act(a) for a in qry.order_by(Activiteit.datum.is_(None), Activiteit.datum).all()]


def _act_data(body: ActBody) -> dict:
    data = body.model_dump()
    for fk in ("organisatie_id", "contactpersoon_id", "krachtenveld_id"):
        if data.get(fk):
            data[fk] = _uuid(data[fk])
    return data


@router.post("/activiteiten", status_code=201)
def create_act(body: ActBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = Activiteit(tenant_id=user.tenant_id, **_act_data(body))
    db.add(a); db.commit(); db.refresh(a)
    return _act(a)


@router.patch("/activiteiten/{act_id}")
def update_act(act_id: str, body: ActBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.query(Activiteit).filter(Activiteit.id == _uuid(act_id),
                                    Activiteit.tenant_id == user.tenant_id).first()
    if not a:
        raise HTTPException(404, "Activiteit niet gevonden")
    for k, v in _act_data(body).items():
        setattr(a, k, v)
    db.commit(); db.refresh(a)
    return _act(a)


@router.delete("/activiteiten/{act_id}", status_code=204)
def delete_act(act_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.query(Activiteit).filter(Activiteit.id == _uuid(act_id),
                                    Activiteit.tenant_id == user.tenant_id).first()
    if not a:
        raise HTTPException(404, "Activiteit niet gevonden")
    db.delete(a); db.commit()


# ── RAPPORTAGE ───────────────────────────────────────────────────────────────────
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = user.tenant_id
    def cnt(model, *filt):
        return db.query(func.count(model.id)).filter(model.tenant_id == t, *filt).scalar() or 0

    rso_count = cnt(Organisatie, Organisatie.soort == "RSO")
    vvt_count = cnt(Organisatie, Organisatie.soort == "VVT")

    per_betrouwbaarheid = dict(
        db.query(Organisatie.betrouwbaarheid, func.count(Organisatie.id))
          .filter(Organisatie.tenant_id == t, Organisatie.soort == "VVT")
          .group_by(Organisatie.betrouwbaarheid).all())

    # aanbieders per RSO
    per_rso = db.query(Organisatie.rso_naam, func.count(Organisatie.id))\
                .filter(Organisatie.tenant_id == t, Organisatie.soort == "VVT")\
                .group_by(Organisatie.rso_naam).order_by(func.count(Organisatie.id).desc()).all()

    # stakeholders per kwadrant
    quad = {"Actief betrekken": 0, "Tevreden houden": 0, "Mee nemen": 0, "Informeren": 0}
    for s in db.query(Stakeholder).filter(Stakeholder.tenant_id == t).all():
        quad[_quadrant(s.invloed, s.betrokkenheid)] += 1

    houding = dict(db.query(Stakeholder.houding, func.count(Stakeholder.id))
                     .filter(Stakeholder.tenant_id == t).group_by(Stakeholder.houding).all())

    return {
        "rso_count": rso_count,
        "aanbieder_count": vvt_count,
        "contactpersoon_count": cnt(Contactpersoon),
        "krachtenveld_count": cnt(Krachtenveld),
        "stakeholder_count": cnt(Stakeholder),
        "open_activiteiten": cnt(Activiteit, Activiteit.status == "open"),
        "betrouwbaarheid": {k or "Onbekend": v for k, v in per_betrouwbaarheid.items()},
        "aanbieders_per_rso": [{"rso": r or "Onbekend", "aantal": n} for r, n in per_rso],
        "kwadranten": quad,
        "houding": {k or "Onbekend": v for k, v in houding.items()},
    }
