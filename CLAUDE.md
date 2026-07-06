# CLAUDE.md — Rhadix CRM projectgeheugen

Lees dit bestand aan het begin van elke sessie. Werk de sessie-log bij aan het einde.

## Project
**Rhadix CRM** — vierde applicatie van het Rhadix-platform. Stakeholder-/relatiebeheer met
krachtenveld-analyse (invloed × betrokkenheid) rond RSO's en VVT-zorgaanbieders.
- **Repo:** https://github.com/Rhadix2026/rhadix-crm
- **Stack:** FastAPI · React/Vite · PostgreSQL · Docker · GHCR
- **Zuster-apps:** Rhadix-datavalidatie, rhadix-uitvraag, Rhadix-datastation
- **Server:** `46.224.224.26` (Hetzner), nginx reverse proxy, gedeeld wildcard cert `*.rhadix.nl`

## Poorten
| Omgeving | Frontend | Backend | Subdomein (voorstel) |
|---|---|---|---|
| Productie | 5182 | 8018 | crm.rhadix.nl |
| Staging   | 5183 | 8019 | crm-staging.rhadix.nl |

(Bestaand: DV 5174/8010·5175/8011 · Uitvraag 5176/8012·5177/8013 · Datastation 5180/8016·5181/8017.)

## Branch-strategie
- `staging` push → auto-deploy staging.
- Versie-tag `v*.*.*` op `main` → productie via GitHub Actions, handmatige goedkeuring + rollback.
- Na main-wijziging ook naar staging mergen.

## Auth / identiteit
Resource-server: accepteert centraal SureSync ID-token (RS256, `CENTRAL_JWT_PUBLIC_KEY` +
issuer `suresync-id`) via header of `rhadix_sso`-cookie, met JIT-provisioning. Lokale HS256-login
blijft werken (admin@rhadix.nl). Niet-destructieve admin-bootstrap (nooit TRUNCATE), `AUTH_RESET=0`
slaat over.

## Belangrijke bestanden
| Bestand | Inhoud |
|---|---|
| `backend/app/models/crm_models.py` | Organisatie, Contactpersoon, Krachtenveld, Stakeholder, Activiteit |
| `backend/app/routers/crm.py` | CRUD + dashboard; kwadrant-afleiding `_quadrant()` |
| `backend/app/bootstrap.py` | niet-destructieve admin + idempotente seed (`rso_seed.json`) + voorbeeld-krachtenveld |
| `backend/app/seed/rso_seed.json` | 17 RSO's, 152 aanbieders, 68 contactpersonen (uit Excel) |
| `frontend/src/pages/Krachtenveld.jsx` | matrix invloed × betrokkenheid + canvas-blokken |
| `frontend/src/brand.js` + `index.css` | merk-laag rhadix/suresync, env-gestuurd palet |

## Seed-data
Bron: `RSO_VVT_mapping_indicatief_Nederland_met_contactpersonen.xlsx` (peildatum 2026-06-19).
Indicatief — valideren vóór formeel gebruik. Idempotent; `CRM_SEED=0` slaat over.

## Bekende afspraken / lessen
- Git lock-files in sandbox: altijd naar `/tmp/` klonen, nooit naar de gemounte map.
- Vóór pushen frontend-wijzigingen: altijd `npm run build` lokaal draaien.
- Nooit secrets/sleutels committen; centrale RS256-sleutel via GitHub Secret / .env.
- Productie ongemoeid tijdens bouw — alles eerst op staging.
- **nginx op de server**: alle vhosts staan in ÉÉN bestand `/etc/nginx/sites-enabled/rhadix` (een aparte kopie, GEEN symlink naar sites-available). Wijzig altijd de **enabled**-versie; `sites-available/rhadix` is verouderd/divergerend. Cert: `/etc/ssl/rhadix/rhadix.pem` + `.key`. Per app twee server-blokken (80→301 https, 443 met `location /api/`→backend en `location /`→frontend).

## Activatie & toegang
- **Staging:** https://crm-staging.rhadix.nl — nginx-blok in `sites-enabled/rhadix` (fe:5183 be:8019).
- **Productie:** https://crm.rhadix.nl (fe:5182 be:8018) — vhost + DNS + PROD-secrets vereist.
- **Login (alle apps gelijk):** `admin@rhadix.nl` / `Rhadixvalidatie26!` (gelekt — bij gelegenheid platformbreed roteren).
- **GitHub-secrets** per omgeving: `*_DB_PASSWORD`, `*_JWT_SECRET_KEY`, `*_ADMIN_PASSWORD`, `*_SSH_KEY/HOST/USER`. Centrale publieke SSO-sleutel zit als default in de compose-bestanden (geen secret nodig).
- **Server-map:** `/opt/crm-app` (compose + .env per omgeving).

## Sessie-log
| Datum | Wijziging |
|---|---|
| 2026-07-06 | Meerdere Rhadix-accounthouders per relatie **én** contactpersoon (was: 1 enkele). Model: koppeltabellen `crm_organisatie_accounthouders` + `crm_contactpersoon_accounthouders` (M2M `extra_accounthouders`); contactpersoon kreeg eigen primaire `accounthouder_id`. Keuze: **primair + extra** (primair blijft leidend voor rapportage). bootstrap `_ensure_columns` vult cp.accounthouder_id; koppeltabellen via `create_all` (bestaande data intact). Router: `_org`/`_cp` serialiseren extra_accounthouders(+ids), bodies krijgen `extra_accounthouder_ids` (cp ook `accounthouder_id`), create/update vullen M2M tenant-gescoopt (onbekende ids stil genegeerd). Frontend: herbruikbare `TeamMultiSelect` (checkboxes) in relatie- en contactpersoon-formulier + weergave in detail. 25 backend-tests groen, build groen. Naar staging gepusht (dcb0254) — CI + deploy-staging groen, health ok. Prod ongemoeid. TODO: na akkoord op staging productie-release via versietag. |
| 2026-06-23 | LIVE op staging: `crm-staging.rhadix.nl` geactiveerd (GitHub-secrets, nginx-blok in `sites-enabled/rhadix`, Cloudflare DNS). Deploy groen (test+build+deploy+health). Seed bevestigd op staging-DB (17/152/68 + 1 krachtenveld/8 stakeholders). Admin-wachtwoord gelijkgetrokken met platform (`Rhadixvalidatie26!`). Centrale SSO-publieke sleutel als default in beide compose-bestanden. Release v0.1.0 → productie. |
| 2026-06-23 | Repo opgezet: volledige Rhadix-conforme CRM (FastAPI+Vite+Postgres+Docker), unified identity (centraal RS256-token + JIT), merk-laag rhadix/suresync. Datamodel + CRUD voor relaties/contacten/krachtenveld/stakeholders/opvolging + dashboard. Seed uit Excel (17 RSO's, 152 aanbieders, 68 contacten) + voorbeeld-krachtenveld GERRIT (8 stakeholders). 13 backend-tests groen, frontend build groen. CI + staging/prod-deploy workflows (poorten 5182/8018 · 5183/8019). Vierde tegel toegevoegd aan platform-portal (datavalidatie staging). |
