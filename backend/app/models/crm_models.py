"""
crm_models.py — Rhadix CRM (stakeholder-/relatiebeheer rond RSO's en VVT-aanbieders).

Vier pijlers (v1):
  1. Relatiebeheer  → Organisatie + Contactpersoon
  2. Krachtenveld   → Krachtenveld + Stakeholder (invloed x betrokkenheid)
  3. Opvolging      → Activiteit (taken/afspraken/notities)
  4. Rapportage     → afgeleid via /dashboard

Statuswaarden als simpele strings — geen enum-migratie nodig.
Alle records zijn tenant-gescoped (multi-tenant-klaar).
"""
from __future__ import annotations

import uuid

from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        String, Table, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base, GUID

# Organisatie-soort
SOORT_RSO = "RSO"   # Regionale Samenwerkingsorganisatie
SOORT_VVT = "VVT"   # Zorgaanbieder (VVT/GZ/GGZ/zorggroep)
SOORT_ZKH = "ZKH"      # Ziekenhuis
SOORT_GGZ = "GGZ"      # Geestelijke gezondheidszorg
SOORT_GHZ = "GHZ"      # Gehandicaptenzorg
SOORT_HA  = "HA"       # Huisartsen(organisatie)/zorggroep
SOORT_OVERIG = "OVERIG"  # Revalidatie/overig niet-VVT

# Niveaus / waarden (vrije strings, UI mapt naar kleuren)
NIVEAUS   = ("Hoog", "Middel", "Laag")
HOUDINGEN = ("Positief", "Neutraal", "Onbekend", "Negatief")

# ── Classificatie van relaties en contactmomenten ─────────────────────────────
# Vier assen, bewust uit elkaar gehaald. Relatietype, status en herkomst zeggen
# iets over een persoon en horen op het contact; kanaal en interesse zeggen iets
# over een moment en horen op de activiteit. Eén contact kan meerdere momenten
# hebben, elk met een eigen kanaal en eigen interesse.
#
# Gewone strings, geen ENUM: een waarde erbij is dan een codewijziging en geen
# databasemigratie. Waarden buiten deze lijsten blijven geldig — de bestaande
# gegevens bevatten varianten die we niet weggooien.

# Wat iemand is. Het generieke type staat naast de specifieke, niet ervoor in de
# plaats: wie de sector kent kiest de sector, wie hem niet kent kiest generiek.
RELATIETYPEN = (
    "Zorgorganisatie",
    "VVT", "Ziekenhuis", "GGZ", "Gehandicaptenzorg", "Huisartsenzorg",
    "RSO", "Overheid", "Leverancier", "Adviesbureau", "Kennispartner", "Overig",
)

# Waar iemand in het proces staat. Het enige veld waarvan je de huidige waarde
# wilt filteren, en daarom een kolom en geen activiteit.
STATUSSEN = ("Nieuw", "Lead", "Gekwalificeerd", "In gesprek", "Klant", "Afgesloten")

# Hoe iemand binnenkwam.
HERKOMSTEN = ("Website", "LinkedIn", "Handmatig", "Event/netwerk",
              "Onderzoek", "Verwijzing")

# Via welke oproep dit moment ontstond.
KANALEN = ("Contactformulier", "Kennismaking", "Data Readiness Check",
           "Pilotaanvraag", "Ontwikkelpartner", "Nieuwsbrief", "Overig")

# Waarin iemand geïnteresseerd is. Meerdere toegestaan, komma-gescheiden.
INTERESSES = ("Datagereedheidsscan", "Implementatiegereedheid",
              "Dataregie en realisatie", "AI-gereedheid",
              "Rhadix", "Readiness Check", "Algemeen")


# ── Koppeltabellen: extra Rhadix-accounthouders (many-to-many) ──────────────────
# Naast de primaire `accounthouder_id` kunnen meerdere collega's gekoppeld worden.
organisatie_accounthouders = Table(
    "crm_organisatie_accounthouders", Base.metadata,
    Column("organisatie_id", GUID(), ForeignKey("crm_organisaties.id", ondelete="CASCADE"),
           primary_key=True),
    Column("user_id", GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

contactpersoon_accounthouders = Table(
    "crm_contactpersoon_accounthouders", Base.metadata,
    Column("contactpersoon_id", GUID(), ForeignKey("crm_contactpersonen.id", ondelete="CASCADE"),
           primary_key=True),
    Column("user_id", GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Organisatie(Base):
    """Een RSO óf een VVT-zorgaanbieder. Eén tabel, onderscheiden via `soort`."""
    __tablename__ = "crm_organisaties"

    id            = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    soort         = Column(String(8), nullable=False, default=SOORT_VVT, index=True)
    naam          = Column(String(255), nullable=False, index=True)
    type          = Column(String(255), nullable=True)   # bv. "VVT/GZ/GGZ of zorggroep"
    werkgebied    = Column(String(512), nullable=True)
    cluster       = Column(String(128), nullable=True)
    provincies    = Column(String(255), nullable=True)
    plaats        = Column(String(128), nullable=True)
    kvk           = Column(String(16), nullable=True)
    website       = Column(String(512), nullable=True)
    bron_url      = Column(String(1024), nullable=True)
    bron_opmerking = Column(Text, nullable=True)

    # RSO-specifiek
    aantal_aangesloten = Column(Integer, nullable=True)
    focus_themas       = Column(String(512), nullable=True)

    # VVT-specifiek (indicatieve koppeling aan een RSO)
    rso_naam        = Column(String(255), nullable=True, index=True)
    betrouwbaarheid = Column(String(32), nullable=True)   # Hoog/Midden/Laag
    onderbouwing    = Column(Text, nullable=True)
    actie_validatie = Column(Text, nullable=True)

    # Contact + Rhadix-accounthouder
    email           = Column(String(255), nullable=True)
    linkedin        = Column(String(512), nullable=True)
    accounthouder_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    accounthouder = relationship("User", foreign_keys=[accounthouder_id], viewonly=True)
    extra_accounthouders = relationship("User", secondary=organisatie_accounthouders,
                                        lazy="selectin")
    contactpersonen = relationship("Contactpersoon", back_populates="organisatie",
                                   cascade="all, delete-orphan")
    krachtenvelden  = relationship("Krachtenveld", back_populates="organisatie",
                                   cascade="all, delete-orphan")


class Contactpersoon(Base):
    __tablename__ = "crm_contactpersonen"

    id             = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id      = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    organisatie_id = Column(GUID(), ForeignKey("crm_organisaties.id", ondelete="SET NULL"), nullable=True, index=True)

    categorie      = Column(String(64), nullable=True)    # RSO / VVT / Leverancier
    organisatie_naam = Column(String(255), nullable=True) # vrije tekst (ook als geen FK)
    rso_regio      = Column(String(255), nullable=True)
    rolniveau      = Column(String(128), nullable=True)   # Bestuur/directie, IV/ICT, ...
    naam           = Column(String(255), nullable=True)
    functie        = Column(String(255), nullable=True)
    email          = Column(String(255), nullable=True)
    linkedin       = Column(String(512), nullable=True)
    telefoon       = Column(String(64), nullable=True)
    bron_url       = Column(String(1024), nullable=True)
    bron_type      = Column(String(128), nullable=True)
    zekerheid      = Column(String(32), nullable=True)    # Hoog/Middel/Laag
    # Waar deze persoon in het proces staat; zie STATUSSEN.
    status         = Column(String(32), nullable=True, index=True)
    # De pagina van de eerste aanraking. Wordt niet overschreven: latere
    # pagina's komen op de activiteit terecht.
    bronpagina     = Column(String(255), nullable=True)
    opmerking      = Column(Text, nullable=True)

    # Rhadix-accounthouder(s): primair + extra teamleden
    accounthouder_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organisatie = relationship("Organisatie", back_populates="contactpersonen")
    accounthouder = relationship("User", foreign_keys=[accounthouder_id], viewonly=True)
    extra_accounthouders = relationship("User", secondary=contactpersoon_accounthouders,
                                        lazy="selectin")


class Krachtenveld(Base):
    """Krachtenveld-analyse rond één organisatie (meestal een RSO)."""
    __tablename__ = "crm_krachtenvelden"

    id             = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id      = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    organisatie_id = Column(GUID(), ForeignKey("crm_organisaties.id", ondelete="CASCADE"), nullable=True, index=True)

    titel          = Column(String(255), nullable=False)
    regio          = Column(String(255), nullable=True)

    # Besluitvormingsstructuur
    bestuurlijk_orgaan    = Column(String(255), nullable=True)
    operationeel_orgaan   = Column(String(255), nullable=True)
    besluitvormingsproces = Column(Text, nullable=True)
    beslissingsfrequentie = Column(String(255), nullable=True)

    # Kwalitatieve velden (vrije tekst / regels gescheiden door newline)
    kernopgave        = Column(Text, nullable=True)
    beslissingsdrivers = Column(Text, nullable=True)
    belemmeringen     = Column(Text, nullable=True)
    kansen            = Column(Text, nullable=True)
    waarde            = Column(Text, nullable=True)
    volgende_stappen  = Column(Text, nullable=True)
    notities          = Column(Text, nullable=True)

    eigenaar          = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organisatie  = relationship("Organisatie", back_populates="krachtenvelden")
    stakeholders = relationship("Stakeholder", back_populates="krachtenveld",
                                cascade="all, delete-orphan", order_by="Stakeholder.created_at")


class Stakeholder(Base):
    """Een stakeholder binnen een krachtenveld, geplot op invloed x betrokkenheid."""
    __tablename__ = "crm_stakeholders"

    id              = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    krachtenveld_id = Column(GUID(), ForeignKey("crm_krachtenvelden.id", ondelete="CASCADE"), nullable=False, index=True)

    naam               = Column(String(255), nullable=False)
    rol                = Column(String(255), nullable=True)
    verantwoordelijkheden = Column(Text, nullable=True)
    doelen_belangen    = Column(Text, nullable=True)

    invloed        = Column(String(16), nullable=True, default="Middel")  # Hoog/Middel/Laag
    betrokkenheid  = Column(String(16), nullable=True, default="Middel")  # Hoog/Middel/Laag
    houding        = Column(String(16), nullable=True, default="Onbekend")  # Positief/Neutraal/Onbekend/Negatief
    email          = Column(String(255), nullable=True)
    linkedin       = Column(String(512), nullable=True)

    argumenten     = Column(Text, nullable=True)
    belemmeringen  = Column(Text, nullable=True)
    aanpak         = Column(Text, nullable=True)
    laatste_contact = Column(Text, nullable=True)
    volgende_stap  = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    krachtenveld = relationship("Krachtenveld", back_populates="stakeholders")


class Activiteit(Base):
    """Opvolging: taak, afspraak of notitie gekoppeld aan een relatie/contact/krachtenveld."""
    __tablename__ = "crm_activiteiten"

    id              = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    organisatie_id  = Column(GUID(), ForeignKey("crm_organisaties.id", ondelete="SET NULL"), nullable=True, index=True)
    contactpersoon_id = Column(GUID(), ForeignKey("crm_contactpersonen.id", ondelete="SET NULL"), nullable=True)
    krachtenveld_id = Column(GUID(), ForeignKey("crm_krachtenvelden.id", ondelete="SET NULL"), nullable=True)

    titel        = Column(String(255), nullable=False)
    soort        = Column(String(32), nullable=False, default="taak")  # taak/afspraak/notitie
    omschrijving = Column(Text, nullable=True)
    status       = Column(String(16), nullable=False, default="open", index=True)  # open/afgerond
    # Wat er op dit moment precies gebeurde. Op de activiteit en niet op het
    # contact, zodat een tweede aanvraag de eerste niet wist.
    kanaal       = Column(String(64), nullable=True, index=True)
    interesse    = Column(String(255), nullable=True)   # komma-gescheiden
    bronpagina   = Column(String(255), nullable=True)
    campagne     = Column(String(255), nullable=True)   # bron/medium/campagne
    datum        = Column(Date, nullable=True)
    eigenaar     = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
