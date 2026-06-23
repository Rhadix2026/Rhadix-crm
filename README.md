# Rhadix CRM

Stakeholder- en relatiebeheer voor het Rhadix-platform, met **krachtenveld-analyse**
(invloed × betrokkenheid) rond **RSO's** (Regionale Samenwerkingsorganisaties) en
**VVT-zorgaanbieders**. Vierde applicatie naast Datavalidatie, Uitvraag en Datastation —
zelfde architectuur, huisstijl en centrale identiteit.

## Functionaliteit (v1)
- **Relatiebeheer** — RSO's en zorgaanbieders met indicatieve mapping, betrouwbaarheid en bron.
- **Krachtenveld** — stakeholders op de matrix *invloed × betrokkenheid* (kwadranten
  Tevreden houden / Actief betrekken / Informeren / Mee nemen), houding t.o.v. Rhadix,
  beslissingsdrivers, belemmeringen, kansen, waarde en volgende stappen.
- **Opvolging** — taken, afspraken en notities per relatie.
- **Rapportage** — dashboard met kengetallen, aanbieders per RSO en stakeholders per kwadrant.

## Stack
FastAPI · React/Vite · PostgreSQL · Docker · GHCR. Resource-server binnen het platform:
accepteert het centrale **SureSync ID**-token (RS256/JWKS) én een eigen lokale login (HS256)
zodat de admin altijd kan inloggen.

## Lokaal draaien
```bash
# Backend
cd backend && pip install -r requirements-dev.txt && uvicorn app.main:app --reload
# Frontend
cd frontend && npm install && npm run dev
```
Of met Docker: `docker compose up --build` → frontend op http://localhost:5173.

Standaard login: `admin@rhadix.nl` / `Rhadixcrm26!` (override via `RHADIX_ADMIN_PASSWORD`).

## Seed
Bij eerste start laadt de app indicatieve RSO/VVT-data + contactpersonen uit
`backend/app/seed/rso_seed.json` (afgeleid uit de aangeleverde Excel) en één uitgewerkt
voorbeeld-krachtenveld (GERRIT). Idempotent; uitzetten met `CRM_SEED=0`.

## Poorten
| Omgeving | Frontend | Backend |
|---|---|---|
| Productie | 5182 | 8018 |
| Staging   | 5183 | 8019 |

## Branch-strategie
`staging` → auto-deploy (staging). Versie-tag `v*.*.*` op `main` → productie via
GitHub Actions met handmatige goedkeuring + automatische rollback. Zie `DEPLOYMENT` in CLAUDE.md.
