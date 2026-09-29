# Definitief datamodel — classificatie van websitecontacten

**Datum:** 29-09-2026 · **Status:** specificatie ter goedkeuring. **Nog niets
geïmplementeerd, geen migratie, geen release.**

Volgt op `VOORSTEL-CLASSIFICATIE-WEBSITECONTACTEN.md` en verwerkt de zeven besluiten van
29-09-2026.

---

## 1. De zes nieuwe kolommen

Alle zes **nullable**, geen defaults, geen `NOT NULL`. Bestaande rijen blijven ongewijzigd
en geldig; er is geen backfill nodig om de migratie te laten slagen.

### `crm_contactpersonen` — twee erbij

| Kolom | Type | Index | Waarom |
|---|---|---|---|
| `status` | `varchar(32)` | ja | Waar staat deze persoon in het proces. Dit is het enige veld waarvan je de *huidige* waarde wilt filteren — "toon alle leads" — en dat vraagt een kolom, geen activiteit. |
| `bronpagina` | `varchar(255)` | nee | De pagina van de **eerste** aanraking. Wordt nooit overschreven; latere pagina's komen op de activiteit. |

Bestaande velden die hun rol houden: **`categorie` = relatietype**, **`bron_type` =
herkomst**, `bron_url`, `rso_regio`, `rolniveau`, `zekerheid`, `opmerking`.

### `crm_activiteiten` — vier erbij

| Kolom | Type | Index | Waarom |
|---|---|---|---|
| `kanaal` | `varchar(64)` | ja | Via welke CTA dit moment ontstond |
| `interesse` | `varchar(255)` | nee | Welke dienst(en); komma-gescheiden, meerdere toegestaan |
| `bronpagina` | `varchar(255)` | nee | De pagina van **dít** moment |
| `campagne` | `varchar(255)` | nee | UTM, compact; staat nu nog los in de omschrijvingstekst |

Geen nieuwe tabellen. Geen koppeltabel voor interesses: meerdere activiteiten leveren dat
al, elk met eigen datum en eigen context.

### De migratie

```sql
ALTER TABLE crm_contactpersonen ADD COLUMN status      varchar(32);
ALTER TABLE crm_contactpersonen ADD COLUMN bronpagina  varchar(255);
CREATE INDEX ix_crm_contactpersonen_status ON crm_contactpersonen (status);

ALTER TABLE crm_activiteiten    ADD COLUMN kanaal      varchar(64);
ALTER TABLE crm_activiteiten    ADD COLUMN interesse   varchar(255);
ALTER TABLE crm_activiteiten    ADD COLUMN bronpagina  varchar(255);
ALTER TABLE crm_activiteiten    ADD COLUMN campagne    varchar(255);
CREATE INDEX ix_crm_activiteiten_kanaal ON crm_activiteiten (kanaal);
```

Zes `ADD COLUMN` zonder default en zonder `NOT NULL`: PostgreSQL herschrijft de tabel dan
niet en de lock is verwaarloosbaar. Op 445 contacten en 3 activiteiten is dit sowieso een
kwestie van milliseconden.

---

## 2. De waardenlijsten

In `crm_models.py`, naast de bestaande `SOORT_*`-constanten. Geen PostgreSQL-`ENUM`.

### Relatietype — `crm_contactpersonen.categorie`

Het generieke type komt **naast** de bestaande specifieke typen, niet in plaats daarvan.
Wie de sector kent, kiest de sector; wie hem niet kent, kiest `Zorgorganisatie`.

```python
RELATIETYPEN = (
    "Zorgorganisatie",   # generiek — nieuw, voor wie de sector nog niet weet
    "VVT", "Ziekenhuis", "GGZ", "Gehandicaptenzorg", "Huisartsenzorg",
    "RSO",
    "Overheid",          # nieuw
    "Leverancier",
    "Adviesbureau",      # nieuw
    "Kennispartner",     # nieuw
    "Overig",
)
```

De specifieke typen zijn overgenomen uit wat er nu daadwerkelijk staat — `VVT` (250×),
`Ziekenhuis` (60×), `RSO` (27×), `Huisartsenzorg` (25×), `GGZ` (24×),
`Gehandicaptenzorg` (15×), `Leverancier` (10×), `Overig` (2×). Samen dekken die 413 van de
445 contacten.

⚠️ De overige 32 contacten staan op varianten die **niet** in de lijst komen:
`Huisartsenorganisatie`, `Revalidatie`, `Revalidatiezorg`,
`Geestelijke Gezondheidszorg (GGZ)`, `Universitair Medisch Centrum`, `Diagnostiek`,
`Ambulancezorg`, `Ambulancezorg (RAV)`, `Publieke gezondheid (GGD)`,
`Publieke gezondheidszorg`, `Farmaceutische zorg (apothekers)`,
`Paramedische zorg (fysiotherapie)`, `Huisartsenzorg (gezondheidscentra)`,
`Geestelijke Gezondheidszorg (GGZ) / beschermd wonen`.

Die **blijven gewoon staan** — het veld blijft een `varchar`, dus een waarde buiten de
lijst is geldig. Ze verschijnen alleen niet in de keuzelijst. Wie zo'n contact opent en
opslaat zonder de categorie aan te raken, verandert er niets aan. Opruimen is later, en
apart.

### Status — `crm_contactpersonen.status` *(nieuw)*

```python
STATUSSEN = ("Nieuw", "Lead", "Gekwalificeerd", "In gesprek", "Klant", "Afgesloten")
```

### Herkomst — `crm_contactpersonen.bron_type`

```python
HERKOMSTEN = ("Website", "LinkedIn", "Handmatig", "Event/netwerk",
              "Onderzoek", "Verwijzing")
```

⚠️ De bestaande waarden — `RegioRadar` (5×), `Organisatiepagina` (4×),
`Vakmedia (Skipr)`, `Nieuwsbericht`, `Teampagina` en de rest — **blijven ongewijzigd
staan**, conform besluit 4. Geen migratie. Ook hier: buiten de lijst is geldig, alleen niet
in de keuzelijst.

### Kanaal — `crm_activiteiten.kanaal` *(nieuw)*

```python
KANALEN = ("Contactformulier", "Kennismaking", "Data Readiness Check",
           "Pilotaanvraag", "Ontwikkelpartner", "Nieuwsbrief", "Overig")
```

`Ontwikkelpartner` staat erbij omdat de homepage die knop letterlijk heeft
("Word ontwikkelpartner") en dat een ander gesprek is dan een kennismaking.

### Interesse — `crm_activiteiten.interesse` *(nieuw)*

```python
INTERESSES = ("Datagereedheidsscan", "Implementatiegereedheid",
              "Dataregie en realisatie", "AI-gereedheid",
              "Rhadix", "Readiness Check", "Algemeen")
```

Opgeslagen als komma-gescheiden tekst wanneer er meer dan één is. Bij een formulierinzending
is er altijd precies één; meerdere ontstaan pas als iemand handmatig aanvult.

---

## 3. Mapping van de CTA's

De site heeft per pagina drie tot vier knoppen die alle op `contact.html` uitkomen. Om ze
te onderscheiden krijgen ze een parameter:

```
contact.html?van=<pagina>&cta=<kanaal>
```

Het contactformulier leest die uit en stuurt ze mee, samen met de UTM-waarden die het
script al in `sessionStorage` bewaart.

| # | CTA | `van` | `cta` | Kanaal | Interesse | Status |
|---|---|---|---|---|---|---|
| 1 | Algemene kennismaking — knop in de kop, elke pagina | *pagina zelf* | `kennismaking` | Kennismaking | Algemeen | Nieuw |
| 2 | Contact vanuit **Diensten** | `diensten` | `contact` | Contactformulier | Algemeen | Nieuw |
| 3 | Contact vanuit **Expertise** | `expertise` | `contact` | Contactformulier | Algemeen | Nieuw |
| 4 | **Rhadix** — "Bespreek een mogelijke pilot" | `rhadix` | `pilot` | Pilotaanvraag | Rhadix | Nieuw |
| 5 | **Data Readiness Check** — rapport opvragen | `data-readiness` | *n.v.t.* | Data Readiness Check | Readiness Check | **Lead** |
| 6 | **Datagereedheidsscan** — "Bespreek een Datagereedheidsscan" | `datagereedheidsscan` | `dienst` | Kennismaking | Datagereedheidsscan | Nieuw |
| 7 | **Implementatiegereedheid** — "Onderzoek uw implementatiegereedheid" | `implementatiegereedheid` | `dienst` | Kennismaking | Implementatiegereedheid | Nieuw |
| 8 | **Dataregie en realisatie** — "Bespreek ondersteuning bij de uitvoering" | `dataregie-realisatie` | `dienst` | Kennismaking | Dataregie en realisatie | Nieuw |
| 9 | **AI-gereedheid** — "Laat uw AI-gereedheid onderzoeken" | `ai-gereedheid` | `dienst` | Kennismaking | AI-gereedheid | Nieuw |
| 10 | Contact vanuit **Inzichten** | `inzichten` | `contact` | Contactformulier | Algemeen | Nieuw |
| 11 | Contact vanuit **Over ons** | `over-ons` | `contact` | Contactformulier | Algemeen | Nieuw |
| 12 | **Algemeen contactformulier** — direct op contact.html | `contact` of leeg | *geen* | Contactformulier | Algemeen | Nieuw |
| 13 | Homepage — "Word ontwikkelpartner" | `index` | `ontwikkelpartner` | Ontwikkelpartner | Rhadix | Nieuw |
| 14 | Na de check — "Bespreek mijn uitslag" | `data-readiness` | `uitslag` | Kennismaking | Readiness Check | **Lead** |

**Het onderscheid dat u vroeg**, met rij 4, 3 en 1: *Rhadix → pilot* levert kanaal
`Pilotaanvraag` met interesse `Rhadix`; *Expertise → contact* levert `Contactformulier`
met `Algemeen`; *Home → kennismaking* levert `Kennismaking` met `Algemeen`. Drie
verschillende combinaties, alle drie terug te vinden op de activiteit.

### Waarom alleen 5 en 14 status Lead krijgen

Wie een rapport opvraagt of zijn uitslag wil bespreken, heeft de check dóórlopen en
daarmee getoond waar hij staat. Dat is inhoudelijk een lead. Wie het contactformulier
invult, is eerst gewoon **Nieuw** — de kwalificatie is dan aan u, niet aan een formulier.

### UTM

`utm_source`, `utm_medium`, `utm_campaign`, `utm_content` en `utm_term` worden al door het
script bewaard voor de duur van het bezoek. Ze gaan mee met beide endpoints en komen samen
in `crm_activiteiten.campagne`, compact:

```
linkedin/cpc/datagereedheid-najaar-2026
```

Alleen de ingevulde delen, gescheiden door `/`. De volledige set blijft daarnaast leesbaar
in `omschrijving`, zoals nu al bij de Readiness Check. Voor toekomstige
LinkedIn-campagnes hoeft er dus niets bij.

---

## 4. Wat er bij een inzending wordt vastgelegd

### Voorbeeld: iemand klikt op Rhadix → "Bespreek een mogelijke pilot"

URL: `contact.html?van=rhadix&cta=pilot` · formulier ingevuld met naam, e-mail,
organisatie, telefoon, bericht.

**`crm_organisaties`** — alleen als de naam nog niet exact bestaat:

| Veld | Waarde |
|---|---|
| `naam` | uit het formulier |
| `soort` | `OVERIG` |
| `bron_opmerking` | `Automatisch aangemaakt vanuit het contactformulier op de website.` |
| `betrouwbaarheid` | `Laag` |
| alle overige | **leeg** — geen werkgebied, geen rso_naam, geen provincies |

**`crm_contactpersonen`** — alleen als het e-mailadres nog niet bestaat:

| Veld | Waarde |
|---|---|
| `naam`, `email`, `telefoon` | uit het formulier |
| `organisatie_id` | verwijzing naar de organisatie hierboven |
| `organisatie_naam` | uit het formulier |
| **`categorie`** | **leeg** — het relatietype is onbekend en wordt niet geraden |
| **`status`** | `Nieuw` |
| **`bron_type`** | `Website` |
| **`bronpagina`** | `rhadix` |
| `bron_url` | `https://rhoderlandengroep.nl/rhadix.html` |
| `zekerheid` | `Hoog` — de bezoeker vulde het zelf in |
| `opmerking` | `Aangemeld via het contactformulier op de website.` |
| `rso_regio`, `rolniveau`, `functie`, `linkedin` | **leeg** |

**`crm_activiteiten`** — **altijd**, ook bij een bestaand contact:

| Veld | Waarde |
|---|---|
| `titel` | `Contactformulier – pilotaanvraag Rhadix` |
| `soort` | `notitie` |
| `status` | `open` |
| `datum` | vandaag |
| `contactpersoon_id`, `organisatie_id` | de koppelingen |
| **`kanaal`** | `Pilotaanvraag` |
| **`interesse`** | `Rhadix` |
| **`bronpagina`** | `rhadix` |
| **`campagne`** | `linkedin/cpc/…` of leeg |
| `omschrijving` | bron, tijdstip, naam, organisatie, e-mail, telefoon, het bericht, en de campagnegegevens voluit |

### Bij de Data Readiness Check

Zelfde opzet, met drie verschillen: `status` wordt **`Lead`**, `bron_type` blijft
`Website` met `bronpagina = data-readiness`, en `kanaal` wordt `Data Readiness Check` met
`interesse = Readiness Check`. De activiteit houdt de bestaande omschrijving met
totaalscore, de vijf dimensiescores en de aandachtspunten — die verandert niet.

### Twee regels die overal gelden

**Een bestaand contact wordt nooit overschreven.** Komt het e-mailadres al voor, dan
worden `categorie`, `status`, `bron_type` en `bronpagina` met rust gelaten — ook als het
contact al `Klant` is. Er komt alleen een activiteit bij. Dat is de hele reden om kanaal en
interesse op de activiteit te zetten.

**Niets wordt geraden.** Geen relatietype uit een domeinnaam, geen sector uit een
organisatienaam, geen regio. Leeg betekent onbekend, en dat is bruikbare informatie.

---

## 5. Wat er met bestaande gegevens gebeurt

| Gegeven | Wat ermee gebeurt |
|---|---|
| 445 contacten met hun `categorie` | **ongewijzigd** — ook de 32 varianten buiten de lijst |
| `bron_type` met RegioRadar, Vakmedia, … | **ongewijzigd** (besluit 4) |
| 288 organisaties met hun `soort` | **ongewijzigd** |
| 3 organisaties op VVT via de website | **ongewijzigd** (besluit 7), later apart |
| Rhoderlanden Groep / Rhoderlandengroep | **niet samengevoegd** (besluit 7) |
| 3 bestaande activiteiten | blijven; de vier nieuwe kolommen zijn leeg |
| 3 Readiness-contacten met lege categorie | blijven leeg; krijgen géén status met terugwerkende kracht |

Geen `UPDATE`, geen `DELETE`, geen hernoeming. De migratie voegt uitsluitend kolommen toe.

---

## 6. Gevolg voor de stagingwijziging

Conform besluit 5 gaat `categorie: "Lead"` **niet** naar productie. Bij implementatie
wijzigt de Readiness-koppeling naar:

```diff
- "categorie": "Lead",
+ "status": "Lead",
+ "bron_type": "Website",
+ "bronpagina": "data-readiness",
```

Twee onderdelen van die stagingwijziging blijven ongewijzigd goed en gaan mee: de
organisatie krijgt `soort: "OVERIG"`, en de keuzelijst krijgt een lege optie zodat een leeg
veld niet meer als RSO wordt getoond.

---

## 7. Wat er gebouwd moet worden

| # | Stap | Waar | Wie |
|---|---|---|---|
| 1 | Alembic-migratie, zes kolommen plus twee indexen | CRM | ✅ ik |
| 2 | Constanten, API-modellen, `_cp()`/`_act()`-serialisatie | CRM | ✅ ik |
| 3 | Frontend: velden, keuzelijsten, filter op status | CRM | ✅ ik |
| 4 | Website: `?van=` en `?cta=` op alle CTA-knoppen, uitlezen in het formulier, UTM meesturen | website | ✅ ik |
| 5 | `/api/contact` schrijft naar het CRM — organisatie, contact, activiteit | rhadix | ✅ ik |
| 6 | Readiness-koppeling: `status` in plaats van `categorie`, plus de nieuwe velden | rhadix | ✅ ik |
| 7 | Tests op alle veertien CTA's, en op het niet-overschrijven van bestaande contacten | — | ✅ ik |
| 8 | End-to-end op staging | — | ✅ ik |
| 9 | Productiereleases CRM + rhadix | — | 🔑 u |

⚠️ **Stap 5 verdient één waarschuwing.** Het contactformulier schrijft nu niets weg. Zodra
dat verandert, komt élke inzending in het CRM — ook spam die door de honeypot en de
snelheidsbegrenzing heen komt. De bestaande beschermingen blijven werken en de CRM-registratie
is nooit blokkerend, maar reken op wat ruis. Een aparte status `Afgesloten` of gewoon
verwijderen is dan de opruiming.

---

## Ter goedkeuring

| | |
|---|---|
| 🔑 | De **zes kolommen** en hun typen |
| 🔑 | De **vijf waardenlijsten** — vooral of de relatietype-lijst de juiste specifieke typen bevat |
| 🔑 | De **mapping van veertien CTA's**, met name dat alleen de Readiness Check status `Lead` geeft |
| 🔑 | Dat een **bestaand contact nooit wordt overschreven**, ook niet zijn status |
| 🔑 | Dat het contactformulier `categorie` **leeg laat** in plaats van iets te raden |
