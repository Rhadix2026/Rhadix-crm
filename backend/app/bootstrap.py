"""bootstrap.py — tabellen aanmaken, niet-destructieve admin borgen, CRM-seed laden."""
from __future__ import annotations

import json
import os
import uuid
from collections import Counter
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models.auth_models import Tenant, User, UserRole
from app.models import crm_models  # noqa: F401  (tabellen registreren)
from app.models.crm_models import (Contactpersoon, Krachtenveld, Organisatie,
                                    Stakeholder)
from app.auth.security import hash_password

SEED_FILE = Path(__file__).parent / "seed" / "rso_seed.json"
PLATFORM_SLUG = "platform"


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    tenant_id = _ensure_admin()
    _seed_crm(tenant_id)


def _ensure_admin() -> uuid.UUID:
    """Niet-destructief: borg admin@rhadix.nl (nooit TRUNCATE). AUTH_RESET=0 slaat over."""
    email = os.getenv("RHADIX_ADMIN_EMAIL", "admin@rhadix.nl")
    password = os.getenv("RHADIX_ADMIN_PASSWORD", "Rhadixcrm26!")
    do = os.getenv("AUTH_RESET", "1").lower() not in ("0", "false", "no")

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == PLATFORM_SLUG).first()
        if not tenant:
            tenant = Tenant(id=uuid.uuid4(), slug=PLATFORM_SLUG, name="Rhadix Platform", is_active=True)
            db.add(tenant); db.flush()
        if do:
            admin = db.query(User).filter(User.email == email).first()
            if admin:
                admin.password_hash = hash_password(password)
                admin.is_active = True
                admin.role = UserRole.PLATFORM_ADMIN
                admin.tenant_id = tenant.id
            else:
                db.add(User(id=uuid.uuid4(), tenant_id=tenant.id, email=email,
                            full_name="Platformbeheerder", password_hash=hash_password(password),
                            role=UserRole.PLATFORM_ADMIN, is_active=True))
        db.commit()
        return tenant.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _seed_crm(tenant_id: uuid.UUID) -> None:
    """Idempotent: alleen laden als er nog geen CRM-organisaties zijn voor deze tenant."""
    if os.getenv("CRM_SEED", "1").lower() in ("0", "false", "no"):
        return
    if not SEED_FILE.exists():
        return
    db = SessionLocal()
    try:
        if db.query(Organisatie).filter(Organisatie.tenant_id == tenant_id).count() > 0:
            return
        data = json.loads(SEED_FILE.read_text(encoding="utf-8"))

        # aantal aanbieders per RSO (voor RSO.aantal_aangesloten)
        per_rso = Counter(a.get("rso") for a in data.get("aanbieders", []) if a.get("rso"))

        org_by_name = {}

        # RSO's
        for r in data.get("rsos", []):
            o = Organisatie(
                tenant_id=tenant_id, soort="RSO", naam=r["naam"], werkgebied=r.get("werkgebied"),
                cluster=r.get("cluster"), provincies=r.get("provincies"), bron_url=r.get("bron_url"),
                bron_opmerking=r.get("bron_opmerking"), aantal_aangesloten=per_rso.get(r["naam"]),
            )
            db.add(o); db.flush()
            org_by_name[o.naam.lower()] = o.id

        # VVT-aanbieders
        for a in data.get("aanbieders", []):
            o = Organisatie(
                tenant_id=tenant_id, soort="VVT", naam=a["naam"], type=a.get("type"),
                rso_naam=a.get("rso"), werkgebied=a.get("werkgebied"), provincies=a.get("provincies"),
                betrouwbaarheid=a.get("betrouwbaarheid"), onderbouwing=a.get("onderbouwing"),
                bron_url=a.get("bron_url"), actie_validatie=a.get("actie_validatie"),
            )
            db.add(o); db.flush()
            org_by_name.setdefault(o.naam.lower(), o.id)

        # Contactpersonen (link op organisatienaam waar mogelijk)
        for c in data.get("contactpersonen", []):
            oid = org_by_name.get((c.get("organisatie") or "").lower())
            db.add(Contactpersoon(
                tenant_id=tenant_id, organisatie_id=oid, categorie=c.get("categorie"),
                organisatie_naam=c.get("organisatie"), rso_regio=c.get("rso_regio"),
                rolniveau=c.get("rolniveau"), naam=c.get("naam"), functie=c.get("functie"),
                email=c.get("email"), telefoon=c.get("telefoon"), bron_url=c.get("bron_url"),
                bron_type=c.get("bron_type"), zekerheid=c.get("zekerheid"), opmerking=c.get("opmerking"),
            ))

        db.commit()
        _seed_voorbeeld_krachtenveld(db, tenant_id, org_by_name)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _seed_voorbeeld_krachtenveld(db, tenant_id, org_by_name) -> None:
    """Eén uitgewerkt voorbeeld-krachtenveld (de RSO-canvas), gekoppeld aan GERRIT."""
    oid = org_by_name.get("gerrit")
    kv = Krachtenveld(
        tenant_id=tenant_id, organisatie_id=oid,
        titel="Krachtenveld GERRIT (voorbeeld)", regio="Groningen, Friesland, Drenthe",
        bestuurlijk_orgaan="Algemeen Bestuur / Raad van Bestuur",
        operationeel_orgaan="Directie / Programmateam",
        besluitvormingsproces="Consensus in AB, voorbereiding in themagroepen",
        beslissingsfrequentie="AB: 4-6x per jaar | Programma's: doorlopend",
        kernopgave=("Regionale gegevensuitwisseling faciliteren\n"
                    "Implementatie landelijke programma's\n"
                    "Stimuleren van datagedreven zorg\n"
                    "Samenwerking en kennisdeling in de regio\n"
                    "Digitale innovatie en standaardisatie"),
        beslissingsdrivers=("Voldoen aan landelijke wet- en regelgeving (Wegiz, KIK-V, EHDS)\n"
                            "Verbeteren van databeschikbaarheid en datakwaliteit\n"
                            "Efficiëntere samenwerking en minder administratieve lasten\n"
                            "Inzicht & sturing op basis van data\n"
                            "Voorbereid zijn op toekomstige verplichtingen en toezicht"),
        belemmeringen=("Beperkte capaciteit en middelen bij aangesloten aanbieders\n"
                       "Complexiteit van bronsystemen en datakwaliteit\n"
                       "Onvoldoende eigenaarschap of prioriteit\n"
                       "Gebrek aan inzicht in eigen data-volwassenheid\n"
                       "Veranderbereidheid en adoptie"),
        kansen=("De Rhadix Index biedt de RSO een objectief en onafhankelijk inzicht in "
                "data-volwassenheid van de regio. Hiermee kan de RSO sturen op "
                "verbeterprioriteiten, voortgang meten en aantoonbaar waarde leveren."),
        waarde=("Regionaal benchmarken met één onafhankelijke score (Rhadix Index)\n"
                "Inzicht in risico's, verbeterkansen en impact\n"
                "Onderbouwde besluitvorming en prioritering\n"
                "Sterkere positionering richting toezichthouders en partners"),
        volgende_stappen=("Kennismaking met key stakeholders\n"
                          "Verdiepend gesprek over uitdagingen en doelen\n"
                          "Pilotvoorstel opstellen voor de regio\n"
                          "Starten met Rhadix Index meting"),
        eigenaar="Rhadix",
    )
    db.add(kv); db.flush()

    # (naam, rol, invloed, betrokkenheid, houding)
    shs = [
        ("Bestuurder / Directeur", "Eindverantwoordelijk voor strategie en regionale samenwerking.",
         "Hoog", "Laag", "Neutraal"),
        ("Programmadirecteur / Manager", "Stuurt programma's aan (bv. gegevensuitwisseling, innovatie).",
         "Hoog", "Laag", "Neutraal"),
        ("Informatiemanager / CIO", "Verantwoordelijk voor informatievoorziening, data-architectuur en informatiemanagement.",
         "Hoog", "Hoog", "Positief"),
        ("Data & Informatiespecialist", "Werkt aan databeschikbaarheid, kwaliteit, standaarden en analyses.",
         "Middel", "Hoog", "Positief"),
        ("Projectleider / Adviseur", "Leidt projecten en initiatieven (bv. KIK-V, EHDS, Wegiz).",
         "Middel", "Hoog", "Onbekend"),
        ("Zorginhoudelijk vertegenwoordiger", "Brengt praktijkperspectief en behoeften van zorgaanbieders in.",
         "Middel", "Hoog", "Onbekend"),
        ("Financieel adviseur / Controller", "Beoordeelt businesscase, budget en financiering.",
         "Middel", "Laag", "Onbekend"),
        ("Communicatie / Relatiemanager", "Verbindt RSO met aangesloten organisaties en stakeholders.",
         "Laag", "Laag", "Onbekend"),
    ]
    for naam, rol, inv, bet, houding in shs:
        db.add(Stakeholder(tenant_id=tenant_id, krachtenveld_id=kv.id, naam=naam, rol=rol,
                           invloed=inv, betrokkenheid=bet, houding=houding))
    db.commit()
