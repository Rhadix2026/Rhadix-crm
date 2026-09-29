# Classificatie van websitecontacten in Rhadix CRM

**Datum:** 29-09-2026 · **Status:** voorstel. **Niets geïmplementeerd, geen databasewijziging.**

Alles hieronder is gemeten in de code en de productiedatabase, niet aangenomen.

---

## De kern van het probleem

`categorie` op de contactpersoon is één tekstveld waar nu al drie verschillende
soorten informatie in zouden moeten passen:

| Wat het zou moeten zeggen | Voorbeeldwaarden |
|---|---|
| **wat iemand ís** | RSO, VVT, Leverancier |
| **waar iemand in het proces staat** | Lead |
| **waar iemand vandaan komt** | — |

Die drie veranderen onafhankelijk van elkaar. Een RSO-contactpersoon die een lead wordt
en later klant, blijft een RSO. Eén veld kan dat niet uitdrukken: wat je ook kiest, je
gooit iets anders weg.

Erger nog: het is een **overschrijfbaar** veld. Iemand die vandaag de Data Readiness Check
doet en over drie maanden een pilot aanvraagt, overschrijft dan zijn eigen
voorgeschiedenis. Precies het punt dat u aansnijdt.

---

## 1. Wat er nu staat

### Het CRM-datamodel

| Tabel | Kolommen | Rol nu |
|---|---|---|
| `crm_organisaties` | 24 | de organisatie; `soort` uit een vaste lijst |
| `crm_contactpersonen` | 19 | de persoon; `categorie` vrije tekst |
| `crm_activiteiten` | 13 | **losse gebeurtenissen**, gekoppeld aan contact én organisatie |
| `crm_krachtenvelden` · `crm_stakeholders` | 19 · 19 | analyse rond een organisatie, staat hier los van |

**`crm_activiteiten` is de tabel die nu al kan wat u wilt.** Elke rij heeft
`organisatie_id`, `contactpersoon_id`, `titel`, `soort`, `omschrijving`, `status`,
`datum` en `eigenaar`. Meerdere rijen per contact, elk met een eigen moment — precies het
model voor contactmomenten.

Hij wordt alleen nog nauwelijks gebruikt: op productie staan **drie** activiteiten, alle
drie `soort = notitie`, `status = open`, en alle drie van vandaag uit de Readiness Check.

### De bestaande velden op de contactpersoon

| Veld | Type | Nu gevuld met | Bruikbaar? |
|---|---|---|---|
| `categorie` | varchar(64) | RSO (27×), VVT, Leverancier, leeg (3×) | ja — **als relatietype** |
| `bron_type` | varchar(128) | "Data Readiness Check", "RegioRadar", "Vakmedia (Skipr)", … | ja — **als herkomst** |
| `bron_url` | varchar(1024) | onderzoeksbron-URL's | ja — **als bronpagina** |
| `rso_regio` | varchar(255) | regio bij RSO-contacten | blijft, alleen voor RSO's |
| `rolniveau` | varchar(128) | "Bestuur/directie", "IV/ICT" | blijft |
| `zekerheid` | varchar(32) | Hoog/Middel/Laag | blijft |
| `opmerking` | text | vrije notitie | blijft |

**Er is geen veld voor status en geen veld voor interesse.** Die ontbreken echt.

### De website-ingangen

Er zijn **twee endpoints** en **drie formulieren**:

| # | Waar | Endpoint | Velden | CRM? |
|---|---|---|---|---|
| 1 | `contact.html` | `/api/contact` | naam, email, organisatie, telefoon, bericht | **nee** |
| 2 | `index.html` (onderaan) | `/api/contact` | idem | **nee** |
| 3 | na de Readiness Check | `/api/contact` | idem + `onderwerp` = naam van de check | **nee** |
| 4 | de Readiness Check zelf | `/api/readiness/report` | naam, email, organisatie, 15 antwoorden, 5 UTM-velden | **ja** |

⚠️ **Alleen de Readiness Check landt in het CRM.** Alle contactformulieren sturen
uitsluitend een e-mail naar `info@rhoderlandengroep.nl`; er wordt niets vastgelegd.
Dat is de grootste gemiste kans in de huidige opzet — belangrijker nog dan de
categorie-kwestie.

Daarnaast: **UTM wordt alleen door de Readiness Check doorgegeven.** Het contactformulier
stuurt geen UTM en geen bronpagina mee, terwijl de site 4 tot 5 CTA-knoppen per pagina
heeft die allemaal op dezelfde `contact.html` uitkomen. Welke knop iemand aanklikte, is nu
niet te achterhalen.

---

## 2. Het voorstel

### Vier assen, elk op zijn eigen plek

```
CONTACTPERSOON                          ACTIVITEIT (meerdere per contact)
├── relatietype   wat iemand is         ├── kanaal      via welke CTA
├── status        waar in het proces    ├── interesse   welke dienst
├── herkomst      hoe binnengekomen     ├── bronpagina  vanaf welke pagina
└── bronpagina    eerste aanraking      └── campagne    UTM
     (eerste, niet laatste)
```

**Relatietype, status en herkomst horen op het contact** — het zijn eigenschappen van de
persoon die langzaam veranderen.

**Kanaal en interesse horen op de activiteit** — het zijn eigenschappen van een *moment*.
Dit is expliciet uw vraag, en het antwoord is ja: zet ze op de activiteit. Iemand die eerst
de Datagereedheidsscan bekijkt en later een pilot aanvraagt, heeft twee interesses en twee
momenten. Op het contact zou de tweede de eerste wissen; als activiteit staan ze naast
elkaar, met datum, en is de opvolghistorie meteen af te lezen.

### De waardenlijsten

**Relatietype** — hergebruikt `categorie`, met een uitgebreide lijst:

`Zorgorganisatie` · `RSO` · `Overheid` · `Leverancier` · `Adviesbureau` ·
`Kennispartner` · `Overig` · *(leeg = onbekend)*

**Status** — nieuw veld:

`Nieuw` · `Lead` · `Gekwalificeerd` · `In gesprek` · `Klant` · `Afgesloten`

**Herkomst** — hergebruikt `bron_type`:

`Website` · `LinkedIn` · `Handmatig` · `Event/netwerk` · `Onderzoek` · `Verwijzing`

⚠️ `bron_type` bevat nu waarden als "RegioRadar" en "Vakmedia (Skipr)". Die zijn allemaal
onderzoek; zie §6 voor hoe ze behouden blijven.

**Kanaal/CTA** — op de activiteit:

`Contactformulier` · `Kennismaking` · `Data Readiness Check` · `Pilotaanvraag` ·
`Nieuwsbrief` · `Overig`

**Interesse/dienst** — op de activiteit, meerdere toegestaan:

`Datagereedheidsscan` · `Implementatiegereedheid` · `Dataregie en realisatie` ·
`AI-gereedheid` · `Rhadix` · `Readiness Check` · `Algemeen`

### Waarom een status-veld en geen statusactiviteit

Status is de enige as waarvan je **de huidige waarde** wilt kunnen filteren — "toon alle
leads". Dat vraagt een veld op het contact. De geschiedenis van statusovergangen komt
vanzelf uit de activiteiten; daar is geen aparte tabel voor nodig zolang niemand om een
audittrail vraagt.

---

## 3. De CTA's van rhoderlandengroep.nl gemapt

| Waar de bezoeker vandaan komt | Kanaal | Interesse | Status bij aanmaak |
|---|---|---|---|
| `contact.html` — algemeen | Contactformulier | Algemeen | Nieuw |
| `index.html` — formulier onderaan | Contactformulier | Algemeen | Nieuw |
| "Plan een kennismaking" (knop in de kop, elke pagina) | Kennismaking | volgt uit de bronpagina | Nieuw |
| `datagereedheidsscan.html` → contact | Kennismaking | Datagereedheidsscan | Nieuw |
| `implementatiegereedheid.html` → contact | Kennismaking | Implementatiegereedheid | Nieuw |
| `dataregie-realisatie.html` → contact | Kennismaking | Dataregie en realisatie | Nieuw |
| `ai-gereedheid.html` → contact | Kennismaking | AI-gereedheid | Nieuw |
| `rhadix.html` → contact | Kennismaking | Rhadix | Nieuw |
| **Data Readiness Check → rapport** | Data Readiness Check | Readiness Check | **Lead** |
| **Na de check: "bespreek mijn uitslag"** | Kennismaking | Readiness Check | **Lead** |

**Het onderscheid dat ertoe doet:** wie alleen een rapport opvraagt, laat gegevens achter —
dat is een *Lead*. Wie het algemene contactformulier invult zonder dienst, is *Nieuw*.
Alleen de laatste twee regels leveren nu iets in het CRM op; de rest verdwijnt in de
mailbox.

### Hoe de bronpagina wordt vastgelegd

De site heeft één contactformulier waar 4 tot 5 knoppen per pagina naartoe wijzen. Om te
weten wélke knop, is een kleine wijziging aan de website nodig:

1. de CTA-knoppen krijgen een parameter, bijvoorbeeld
   `contact.html?van=datagereedheidsscan&cta=kennismaking`;
2. het formulier leest die uit en stuurt ze mee als `bronpagina` en `kanaal`;
3. de UTM-velden die de Readiness Check al kent, gaan ook mee vanuit het contactformulier —
   het script bewaart ze al in `sessionStorage`, dus dat is hergebruik, geen nieuw mechanisme.

Dat is dus **geen CRM-wijziging maar een websitewijziging**, en hij is nodig voordat de
CRM-velden zinvol gevuld kunnen worden.

---

## 4. Wat dit betekent voor de stagingwijziging

De wijziging van gisteren staat op staging in twee repositories en is **niet in strijd**
met dit voorstel — hij is er een deelverzameling van.

| Wat er nu op staging staat | Past het? |
|---|---|
| contact krijgt `categorie: "Lead"` | ⚠️ **nee** — "Lead" is een **status**, geen relatietype |
| organisatie krijgt `soort: "OVERIG"` | ✅ ja, blijft precies zo |
| `rso_regio` blijft leeg | ✅ ja |
| `bron_type = "Data Readiness Check"` | ⚠️ **schuift** — wordt herkomst `Website`, kanaal `Data Readiness Check` |
| lege optie in de keuzelijst | ✅ ja, blijft nodig |
| opmerking ongewijzigd | ✅ ja |

**Mijn advies: breng de stagingwijziging niet los naar productie.** Zou u dat wel doen, dan
schrijft u "Lead" in het categorieveld en moet dat bij de invoering van dit voorstel weer
uit alle records worden gehaald — een datamigratie die u nu nog kunt voorkomen.

De twee onderdelen die wél meteen goed zijn — `soort: OVERIG` en de lege optie in de
keuzelijst — kunnen desgewenst apart mee. Dat is uw afweging; blijven wachten kost alleen
dat nieuwe organisaties intussen VVT blijven krijgen.

---

## 5. Database- en migratiewijzigingen

### Nieuwe kolommen

**`crm_contactpersonen`** — twee erbij:

| Kolom | Type | Toelichting |
|---|---|---|
| `status` | `varchar(32)`, nullable, index | Nieuw/Lead/Gekwalificeerd/In gesprek/Klant/Afgesloten |
| `bronpagina` | `varchar(255)`, nullable | eerste aanraking, wordt niet overschreven |

**`crm_activiteiten`** — vier erbij:

| Kolom | Type | Toelichting |
|---|---|---|
| `kanaal` | `varchar(64)`, nullable | Contactformulier, Kennismaking, … |
| `interesse` | `varchar(255)`, nullable | één of meer diensten, komma-gescheiden |
| `bronpagina` | `varchar(255)`, nullable | pagina van dít moment |
| `campagne` | `varchar(255)`, nullable | UTM, nu nog in de omschrijvingstekst |

Geen nieuwe tabellen. Geen tabel voor interesse-per-contact: de activiteiten leveren dat
al, en een aparte koppeltabel zou alleen zinvol zijn als u interesses los van een moment
wilt kunnen beheren — die behoefte is er nu niet.

**Alle kolommen nullable, geen defaults.** Bestaande rijen blijven ongewijzigd en geldig;
er is geen backfill nodig om de migratie te laten slagen.

### Waardenlijsten: in de code, niet in de database

Gebruik constanten in `crm_models.py`, zoals `SOORT_*` nu al gebeurt — geen `ENUM`-type en
geen referentietabel. Een `ENUM` in PostgreSQL uitbreiden vraagt een migratie voor elke
nieuwe waarde; met een `varchar` plus een lijst in de code is dat een codewijziging. Bij
zeven waarden die af en toe schuiven is dat het verstandige compromis.

### Migratiestappen

1. Alembic-revisie met zes `ADD COLUMN`-opdrachten — alle nullable, dus geen tabelherschrijving en geen lock van betekenis.
2. Constanten en API-modellen uitbreiden.
3. Frontend: velden tonen, keuzelijsten vullen.
4. De Readiness-koppeling vult de nieuwe velden.
5. Optionele, **losse** dataopschoning (§6).

---

## 6. Wat er met de bestaande gegevens gebeurt

**Er gaat niets verloren.** Alleen toevoegen, niets hernoemen of verwijderen.

| Bestaand | Wat ermee gebeurt |
|---|---|
| 27 contacten met `categorie = RSO` | blijven RSO — dat is hun **relatietype**, en dat klopt |
| VVT, Leverancier, Ziekenhuis, GGZ, … (ruim 400) | blijven staan; passen al in de nieuwe lijst of blijven als vrije waarde |
| 3 contacten met lege categorie | blijven leeg = onbekend |
| `bron_type` met "RegioRadar", "Vakmedia (Skipr)", … | **blijft ongewijzigd staan** |
| `bron_url` | ongewijzigd |
| `rso_regio` bij RSO-contacten | ongewijzigd |
| 3 bestaande activiteiten | blijven; de nieuwe kolommen zijn leeg |

Voor `bron_type` zijn er twee wegen. **Aanbevolen:** de bestaande waarden laten staan en
alleen nieuwe contacten de nieuwe herkomstwaarden geven; de oude waarden zijn zelf al
informatief. **Alternatief:** ze normaliseren naar `Onderzoek` en de oorspronkelijke waarde
naar `bron_url` of `opmerking` verplaatsen — dat is een echte datamigratie op ruim 400
records en vraagt een apart akkoord.

Het enige dat écht weg zou moeten, is de "Lead" in het categorieveld — en dat voorkomt u
door de stagingwijziging niet los uit te rollen.

---

## 7. Volgorde als u akkoord gaat

| # | Stap | Waar | Wie |
|---|---|---|---|
| 1 | Waardenlijsten definitief vaststellen | — | 🔑 u |
| 2 | Alembic-migratie, zes kolommen | CRM | ✅ ik |
| 3 | API-modellen en constanten | CRM | ✅ ik |
| 4 | Frontend: velden en keuzelijsten | CRM | ✅ ik |
| 5 | Website: CTA-parameters en UTM op het contactformulier | website | ✅ ik |
| 6 | **`/api/contact` naar het CRM laten schrijven** | rhadix | ✅ ik |
| 7 | Readiness-koppeling vult de nieuwe velden | rhadix | ✅ ik |
| 8 | End-to-end test op staging, alle vier de CTA's | — | ✅ ik |
| 9 | Productiereleases CRM en rhadix | — | 🔑 u |

**Stap 6 is de grootste winst van dit hele voorstel.** Elk bericht via het
contactformulier verdwijnt nu in een mailbox. Dat is geen classificatievraagstuk maar een
gat: er is geen enkele registratie van wie zich meldt, waarvoor, en of er iets mee is
gedaan.

---

## Wat ik van u nodig heb

| | |
|---|---|
| 🔑 | Akkoord op de **vier assen** en hun verdeling over contact en activiteit |
| 🔑 | De **waardenlijsten** — vooral of `Zorgorganisatie` de bestaande VVT/ZKH/GGZ/GHZ/HA vervangt of ernaast komt |
| 🔑 | Of `/api/contact` in het CRM moet gaan schrijven (stap 6) |
| 🔑 | Wat er met de bestaande `bron_type`-waarden gebeurt — laten staan of normaliseren |
| 🔑 | Of de stagingwijziging blijft wachten, of dat `soort: OVERIG` alvast los meegaat |
