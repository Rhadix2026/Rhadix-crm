"""krachtenveld_generator.py — bouwt automatisch een krachtenveld op uit een
standaard RSO-sjabloon én de bestaande contactpersonen van de organisatie."""
from __future__ import annotations

from app.models.crm_models import Contactpersoon, Krachtenveld, Stakeholder

# Standaard RSO-rollen op de matrix — (naam, rol, invloed, betrokkenheid, houding)
STANDAARD_ROLLEN = [
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
    ("Communicatie / Relatiemanager", "Verbindt de RSO met aangesloten organisaties en stakeholders.",
     "Laag", "Laag", "Onbekend"),
]


def _canvas(naam: str, regio: str) -> dict:
    """Standaard canvas-tekst voor een RSO-krachtenveld (te bewerken na generatie)."""
    return dict(
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
        kansen=(f"De Rhadix Index biedt {naam} een objectief en onafhankelijk inzicht in "
                "de data-volwassenheid van de regio. Hiermee kan de RSO sturen op "
                "verbeterprioriteiten, voortgang meten en aantoonbaar waarde leveren aan aangesloten aanbieders."),
        waarde=("Regionaal benchmarken met één onafhankelijke score (Rhadix Index)\n"
                "Inzicht in risico's, verbeterkansen en impact\n"
                "Onderbouwde besluitvorming en prioritering\n"
                "Sterkere positionering richting toezichthouders en partners"),
        volgende_stappen=("Kennismaking met key stakeholders\n"
                          "Verdiepend gesprek over uitdagingen en doelen\n"
                          "Pilotvoorstel opstellen voor de regio\n"
                          "Starten met Rhadix Index meting"),
    )


def _positie_uit_rolniveau(rolniveau: str | None, functie: str | None):
    """Leid (invloed, betrokkenheid) af uit het rolniveau/functie van een contactpersoon."""
    t = f"{rolniveau or ''} {functie or ''}".lower()
    def has(*kw): return any(k in t for k in kw)
    if has("bestuur", "directie", "directeur", "raad van bestuur"):          return ("Hoog", "Laag")
    if has("cio", "informatiemanager", "iv/ict", "ict", "architect",
            "informatievoorziening", "informatiemanagement"):                return ("Hoog", "Hoog")
    if has("data", "analist", "specialist", "kwaliteit"):                    return ("Middel", "Hoog")
    if has("project", "adviseur", "programma", "implementatie"):             return ("Middel", "Hoog")
    if has("zorginhoud", "verpleeg", "behandel", "kwaliteitsverpleeg"):      return ("Middel", "Hoog")
    if has("financ", "controller", "business", "inkoop"):                    return ("Middel", "Laag")
    if has("communicatie", "relatie", "woordvoer", "marketing"):            return ("Laag", "Laag")
    return ("Middel", "Middel")


def genereer_krachtenveld(db, tenant_id, organisatie) -> Krachtenveld:
    """Maak een krachtenveld voor de organisatie: standaard rollen + eigen contactpersonen."""
    regio = organisatie.werkgebied or organisatie.provincies or ""
    kv = Krachtenveld(
        tenant_id=tenant_id, organisatie_id=organisatie.id,
        titel=f"Krachtenveld {organisatie.naam}", regio=regio, eigenaar="Rhadix",
        notities="Automatisch gegenereerd uit standaard RSO-sjabloon + gekoppelde contactpersonen. "
                 "Schaaf invloed/betrokkenheid/houding per stakeholder bij.",
        **_canvas(organisatie.naam, regio),
    )
    db.add(kv); db.flush()

    # 1) Standaard RSO-rollen
    for naam, rol, inv, bet, houding in STANDAARD_ROLLEN:
        db.add(Stakeholder(tenant_id=tenant_id, krachtenveld_id=kv.id, naam=naam, rol=rol,
                           invloed=inv, betrokkenheid=bet, houding=houding))

    # 2) Bestaande contactpersonen van deze organisatie → stakeholders
    contacten = (db.query(Contactpersoon)
                 .filter(Contactpersoon.tenant_id == tenant_id,
                         Contactpersoon.organisatie_id == organisatie.id)
                 .all())
    aantal_contacten = 0
    for c in contacten:
        if not (c.naam or c.functie):
            continue
        inv, bet = _positie_uit_rolniveau(c.rolniveau, c.functie)
        db.add(Stakeholder(
            tenant_id=tenant_id, krachtenveld_id=kv.id,
            naam=c.naam or c.functie, rol=c.functie or c.rolniveau,
            invloed=inv, betrokkenheid=bet, houding="Onbekend",
            laatste_contact=(c.opmerking or ""),
        ))
        aantal_contacten += 1

    db.commit(); db.refresh(kv)
    return kv
