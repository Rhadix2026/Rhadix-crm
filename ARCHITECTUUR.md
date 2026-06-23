# Architectuur — Rhadix CRM

## Plaats in het platform
Rhadix CRM is de **vierde applicatie** in het Rhadix-landschap (Datavalidatie, Uitvraag,
Datastation, CRM). Het is een **resource-server**: geen eigen identiteit nodig, maar het
vertrouwt het centrale **SureSync ID**-token (RS256) van het platform en leest rol +
toegang uit de claims (JIT-provisioning). Daarnaast is er een lokale HS256-login zodat de
beheerder altijd los kan inloggen.

## Datamodel
- **Organisatie** — RSO óf VVT-aanbieder (`soort`), met werkgebied, cluster, provincies en
  (voor VVT) indicatieve RSO-koppeling + betrouwbaarheid/onderbouwing.
- **Contactpersoon** — bestuurlijk/IV-ICT-contact, optioneel gekoppeld aan een organisatie.
- **Krachtenveld** — analyse rond één organisatie: besluitvormingsstructuur, kernopgave,
  beslissingsdrivers, belemmeringen, kansen, waarde, volgende stappen.
- **Stakeholder** — binnen een krachtenveld; invloed/betrokkenheid/houding. Het kwadrant
  wordt afgeleid uit invloed × betrokkenheid.
- **Activiteit** — opvolging (taak/afspraak/notitie) gekoppeld aan relatie/contact/krachtenveld.

Alle records zijn **tenant-gescoped** (multi-tenant-klaar). De seed staat in de
`platform`-tenant, waar de admin op inlogt.

## Auth
- `backend/app/auth/security.py` — HS256 (lokaal) + `decode_central_token` (RS256, issuer-check).
- `backend/app/auth/dependencies.py` — `get_current_user` accepteert bearer-token of
  `rhadix_sso`-cookie; bij RS256 → `_provision_from_claims` (JIT). Rolmapping
  `RHADIX_ADMIN/PLATFORM_ADMIN → PLATFORM_ADMIN`.

## Merk-laag
`frontend/src/brand.js` + `index.css`: `:root` = Rhadix navy (productie), `:root[data-env=staging]`
= salie-groen accent, `:root[data-brand=suresync]` = violet/navy (white-label). Schakelbaar via
de SureSync-knop in de nav (alleen op staging).

## Deploy
Identiek aan de andere apps: `staging`-branch → auto-deploy (poort 5183/8019); tag op `main`
→ productie (5182/8018) met goedkeuring + rollback. Server `/opt/crm-app`, nginx-vhost naar
een subdomein (bv. `crm-staging.rhadix.nl` / `crm.rhadix.nl`), gedeeld wildcard Origin-cert.
