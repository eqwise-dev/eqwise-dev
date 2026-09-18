# Swarm-check www.werkenbijpggm.nl

**Datum:** 18 september 2026
**Uitgevoerd door:** EQwise — swarm van 6 parallelle onderzoeksagents
**Onderwerp:** carrièresite van PGGM (pensioenuitvoeringsorganisatie, Zeist)

---

## 0. Lees dit eerst: wat deze check wel en niet is

De omgeving waarin deze check draaide mocht **geen externe pagina's ophalen** (egress-policy blokkeert `curl` en WebFetch op alle domeinen). Het onderzoek is daarom volledig gebaseerd op **zoekresultaten**: geïndexeerde URL's, page titles en snippets van beide PGGM-domeinen, aggregators, reviewsites en vakpers. Zes agents hebben samen ruim 70 zoekopdrachten uitgevoerd.

**Wel vastgesteld:** welke URL's geïndexeerd zijn, welke page titles er staan, welk domein wint per zoekopdracht, welke bronnen de kandidaatvragen beantwoorden, en hoe PGGM zich verhoudt tot APG, MN, Achmea, a.s.r., NN en Rabobank.

**Niet vastgesteld — vereist een crawl:** HTTP-statuscodes, `rel=canonical`, redirects, `robots.txt`, XML-sitemaps, `hreflang`, `JobPosting`/`FAQPage`/`Organization` structured data, Core Web Vitals, toegankelijkheid, en of vacatures client-side (JavaScript) geladen worden.

Waar hieronder "waarschijnlijk" of "indicatie" staat, is dat een gevolgtrekking uit zoekresultaten — geen waarneming. Dat onderscheid is bewust overal aangehouden.

---

## 1. Managementsamenvatting

De carrièresite van PGGM heeft geen contentprobleem. De employer value proposition is bovengemiddeld (drie waarden opgehaald uit 800+ medewerkersverhalen, de Impact4-campagne, het Grand Café-gesprek met een recruiter vóór het solliciteren) en de arbeidsvoorwaarden zijn sterk. Het probleem is **distributie en structuur**.

Vijf bevindingen, in volgorde van zwaarte:

1. **De carrière-content bestaat twee keer**, op `werkenbijpggm.nl` én op `pggm.nl/werken-bij`, met een 1-op-1 padmapping en letterlijk identieke page titles. Beide domeinen staan zelfstandig in de index en verschijnen in dezelfde resultatenlijst. Er zijn feitelijk vier hostnames met carrière-content.
2. **Het employer-branddomein is de verliezende kant van dat duplicaat.** In 13 van de 14 niet-geforceerde zoekopdrachten wint `pggm.nl`. Het domein dat het merk draagt, bouwt de autoriteit niet op.
3. **Aggregators staan structureel vóór de eigen site** — Jobbird, Magnet.me, Qompas, Indeed en LinkedIn winnen zelfs op de eigen merkclaim "werken bij PGGM". Op stage- en traineeshipqueries verliest PGGM volledig.
4. **Derden beantwoorden de kandidaatvragen.** Salaris komt van Indeed en Glassdoor, het assessment van assessmentoefenen.nl, het hybride model van AWVN en Magnet.me, de sabbatical van MT/Sprout. Voor AI-antwoordmachines is dát de bron, niet PGGM.
5. **De eigen kerncijfers spreken elkaar tegen** op de eigen pagina's: 1.500 versus circa 1.850 versus "bijna 2.000 collega's"; 4,3 / 4,4 / 5,6 / 5,8 miljoen deelnemers. Voor een organisatie waarvan het bestaansrecht nauwkeurigheid is, is dat een geloofwaardigheidsprobleem.

De rode draad: **PGGM betaalt voor employer branding op een domein dat het verkeer niet vasthoudt, en laat de converterende vragen over aan derden.**

---

## 2. Bevindingen per thema

### 2.1 Domeinstructuur — zwaarte: hoog

De padmapping is systematisch: `werkenbijpggm.nl/{pad}` ↔ `pggm.nl/werken-bij/{pad}`. Bevestigd voor vacatures, vakgebieden, arbeidsvoorwaarden, waarom-pggm, young-professionals, traineeship, recruiters en ervaringen.

Identieke titles op beide domeinen, onder meer:

| Titel | pggm.nl | werkenbijpggm.nl |
|---|---|---|
| `PGGM als werkgever \| PGGM` | `/werken-bij` | `/` |
| `Werken bij PGGM. Dit zijn onze vacatures. \| PGGM` | `/werken-bij/vacatures` | `/vacatures` |
| `Onze vakgebieden \| PGGM` | `/werken-bij/vakgebieden` | `/vakgebieden` |
| `Arbeidsvoorwaarden en CAO bij PGGM \| PGGM` | `/werken-bij/arbeidsvoorwaarden` | `/arbeidsvoorwaarden` |

Het is geen exacte kloon: `pggm.nl/werken-bij/ervaringen-van-pggm-ers/` (met streepjes, met slash) tegenover `werkenbijpggm.nl/ervaringen-van-pggmers`, en "Werken bij PGGM. **In een** traineeship" tegenover "Werken bij PGGM **in een** traineeship". Bij een consolidatie is een 1-op-1 redirectmap dus **niet mechanisch af te leiden** — er zijn handmatige uitzonderingen.

`pggm.nl` is bovendien breder: sollicitatieprocedure, contact, 100%-PGGM, DEI, stage, de vakgebieden risk & compliance en pensioen & administratie, en de hele Engelse laag (`/en/career/*`) zijn alleen daar gevonden.

**Er zijn vier hostnames met carrière-content:**
1. `www.pggm.nl/werken-bij/*` — volledig, inclusief vacaturedetails en Engels
2. `www.werkenbijpggm.nl/*` — gedeeltelijke kopie, NL-only
3. `pggm.onlinevacatures.nl` — ATS-domein van een leverancier, geïndexeerd tot op printweergave (`/nl/Vacature/Print/73336`)
4. `jaarbericht.pggm.nl/jaaroverzicht-2024/werken-bij` — subdomein dat meerankt op carrièrequeries

Daarnaast lekt een CMS-hostnaam in de index: `pggm-prod65.adobecqms.net`.

> **Tegenstrijdigheid tussen agents, eerlijk gemeld.** Twee agents vonden wél geïndexeerde vacature-detailpagina's op werkenbijpggm.nl (`/vacatures/vacature?id=a0wQs00000Bg3w1IAB` — "UX Designer | PGGM", plus vijf andere). Een derde agent vond er geen enkele. Waarschijnlijk zijn ze er wél maar ranken ze nauwelijks. Dit is met één crawl te beslechten en het raakt de vraag welk domein de converterende laag bezit.

### 2.2 Zichtbaarheid: wie wint — zwaarte: hoog

Over 14 domeinvergelijkende zoekopdrachten wint `pggm.nl` er 13. In 8 gevallen is `werkenbijpggm.nl` volledig afwezig. Alleen wanneer het domein letterlijk in de zoekopdracht staat, wint het.

Op vacaturegerichte zoekopdrachten winnen aggregators van beide:

| Zoekopdracht | Wie staat bovenaan |
|---|---|
| "werken bij PGGM" vacatures | Jobbird; werkenbijpggm.nl rond positie 6 |
| PGGM DevOps engineer | Jobbird, dan LinkedIn (2×), pas daarna pggm.nl |
| PGGM traineeship | Qompas, Magnet.me, TraineeshipPlaza (2×) vóór de eigen site |
| PGGM stage Zeist | LinkedIn, Stagemarkt, Magnet.me, Afstudeerstage — **geen enkele eigen pagina** |
| PGGM UX designer | Magnet.me (2×), uwstadwerkt, uxwork vóór de eigen site |
| PGGM data analist Zeist | bovenste treffer is een **verlopen vacature** |
| vermogensbeheer vacatures | PGGM ontbreekt volledig; a.s.r. breekt hier wél door |

Dat laatste is inhoudelijk het opvallendst: een van de grootste vermogensbeheerders van Nederland is onvindbaar op het belangrijkste vakterm van het eigen domein.

### 2.3 Technische SEO-hygiëne — zwaarte: middel tot hoog

- **Vacature-URL's zonder functienaam.** Op werkenbijpggm.nl draait elke detailpagina op een Salesforce-record-ID: `/vacatures/vacature?id=a0wQs00000BD6fZIAT`. Op pggm.nl bestaan twee patronen naast elkaar — mét slug (`/vacature/webanalist-zeist-32-36-uur/?id=…`) en zonder (`/vacature/?id=a0w1v00000CZ2mgAAD`). Drie patronen voor één contenttype.
- **Verlopen vacatures blijven geïndexeerd.** `/error-page-vacature-niet-gevonden` ("Oeps, deze vacature bestaat niet meer | PGGM") staat als gewone URL in de index — een indicatie van een 200-status waar een 410 hoort. Op de sterke zoekopdracht "PGGM data analist Zeist" is dít de bovenste treffer.
- **Parameterruis:** `?amp=&id=…`, `?amp=&amp=&amp=…`, non-www-varianten, inconsistente trailing slashes, geïndexeerde facetten (`?education=…&function=…&level=junior`) en paginering (`?p=2`).
- **Legacy-URL's die de actuele pagina's verslaan.** `pggm.nl/werken-bij/Paginas/Veelgestelde-vragen.aspx` (SharePoint-tijdperk) stond op positie 1 boven de moderne `/werken-bij/sollicitatieprocedure`. Ook `/Paginas/Ontwikkelingsmogelijkheden.aspx` leeft nog.
- **Titles:** structureel te kort met dubbele branding — `Contact | PGGM` (14 tekens), `IT. Bij PGGM. | PGGM` (20), `Werken bij PGGM | PGGM` (22). Eén vacaturetitel is juist te lang (81). `Ervaringen van PGGM'ers` mist het suffix. En er staat een niet-gedecodeerde HTML-entity in een title: `Manager Inkoop &amp; Contractmanagement`.
- **Functietitels als intern jargon:** `Klantreis - II - klantreismedewerker`, `Senior 3D Sustainability Specialist – Research`, `Junior DevOps Engineer IM IT Administration & Services`, `Pensioenmedewerker werkgeverszaken StiPP`, `Webanalist Zeist 32-36 uur`. Google for Jobs matcht zwaar op het titelveld; uren, locatie, afdelingscodes en interne merknamen horen daar niet in.

### 2.4 GEO/AEO — zwaarte: hoog

Wie beantwoordt de vragen die kandidaten aan een AI-assistent stellen?

| Vraag | Antwoordende bron |
|---|---|
| Hoe is het om bij PGGM te werken? | Indeed-reviews, Glassdoor, MT/Sprout |
| Wat betaalt PGGM? | Indeed, Glassdoor, Loonwijzer, een cao-PDF |
| Wat houdt het assessment in? | assessmentoefenen.nl (commerciële derde) |
| Hoeveel dagen op kantoor? | AWVN, Magnet.me |
| Hoe lang duurt de procedure? | een verouderde `.aspx`-FAQ |
| Is PGGM een goede werkgever? | Glassdoor (89% aanbeveling, 75 reviews), Indeed |
| Arbeidsvoorwaarden | **de eigen site — het enige thema waar PGGM wint** |

Daar komt bij dat negatieve werkgelegenheidsberichten (FD en Pensioen Pro over 20-25% banenreductie bij pensioenbeheer door het nieuwe pensioenstelsel) permanent in de kennisbasis zitten, **zonder eigen tegencontent**. Een AI die gevraagd wordt naar werken bij PGGM heeft geen ander materiaal.

Entiteitsprobleem: er is een Nederlandstalig Wikipedia-lemma voor PGGM, maar het Engelstalige lemma dat opduikt is *Stichting Pensioenfonds Zorg en Welzijn*. Engelstalige AI-antwoorden over werken bij PGGM leunen daardoor op het pensioenfonds in plaats van op de werkgever — terwijl juist de investment- en quantrollen internationaal werven.

### 2.5 Cijferconsistentie — zwaarte: middel, maar pijnlijk

Naast elkaar in omloop, deels op de eigen pagina's:

- **Collega's:** 1.500 (homepage werkenbijpggm.nl + `100-pggm`) · circa 1.850 (`/waarom-pggm`) · "bijna 2.000" (jaarverslag 2025)
- **Deelnemers:** 4,3 mln · 4,4 mln · 5,6 mln · 5,8 mln
- **Beheerd vermogen:** €246 mld · €249 mld · €255 mld · €256,6 mld

Een deel van het verschil bij deelnemers is verklaarbaar als definitiekwestie (deelnemers inclusief gewezen deelnemers, over alle fondsklanten, versus mensen werkzaam in zorg en welzijn). **Het verschil tussen 1.500 en bijna 2.000 collega's is dat niet** — dat is een verouderd getal dat een derde scheelt, op de homepage van de carrièresite. Een kandidaat die homepage en waarom-pagina naast elkaar legt, ziet twee verschillende bedrijven.

### 2.6 Content en propositie — zwaarte: middel

**Sterk en onderbenut:**
- De drie waarden (vertrouwen, samenwerken, vernieuwen) zijn opgehaald uit 800+ medewerkersverhalen onder begeleiding van INSEAD — meer dan 40% van alle medewerkers deed mee. Dat materiaal ligt er en er is geen verhalenhub.
- Het Grand Café-gesprek: informeel kennismaken met de recruiter of een toekomstige collega vóór het solliciteren. Het meest onderscheidende element in de hele propositie, en het staat in de marge.
- De eigen pensioenregeling: 71% betaald door PGGM, 29% door de werknemer. Voor een pensioenuitvoerder is dit het minst kopieerbare bewijs dat er is, en het staat als bullet in een lijstje.
- De mantelzorgregeling, prominenter gemaakt in de cao — zeer geloofwaardig voor een werkgever in zorg en welzijn, en niet gebruikt in de employer branding.
- Impact4-campagne met "Impactmaker"-visitekaartjes; medewerkers namen die titel over op LinkedIn.

**Gaten:**
- Geen verhalenhub, geen FAQ voor kandidaten, geen sollicitatiehulpcontent, geen employer-blog of podcast
- Geen salarisindicatie in vacatures
- Hybride werken alleen in euro's uitgedrukt, niet in verwachtingen ("hoeveel dagen op kantoor")
- Opleidingsbudget zonder bedrag ("ruim opleidingsbudget")
- Vakgebiedpagina's zijn beschrijvend ("data zijn cruciaal voor onze strategie") in plaats van wervend
- Geen locatiepagina's voor Zeist/regio Utrecht — terwijl aggregators die zoekopdracht volledig pakken

### 2.7 Benchmark — zwaarte: context

| Werkgever | Domeinstrategie | Zichtbaarheid |
|---|---|---|
| **PGGM** | **Gespleten over twee domeinen** | Zwak op non-branded; afwezig op vakgebied-head terms |
| APG | Subdomein `werkenbij.apg.nl` | Sterkste op locatie: eigen pagina's boven de aggregators |
| MN | Eigen domein `werkenbijmn.nl` | Redelijk; nog volledig live ná integratie in PGGM |
| Achmea | `werkenbijachmea.nl` + submerken | Sterk op vakgebied (`/ga-voor-data`, `/ga-voor-it`) |
| a.s.r. | `werkenbijasr.nl` | Hoogste non-branded zichtbaarheid; breekt door op "vermogensbeheer" |
| NN | Drie paden + Workday + submerken | Zwakst; aggregators winnen overal |
| PFZW | Alleen een subfolder | Volledig overgenomen door Indeed en LinkedIn |

Drie lessen: **geen enkele benchmark-partij heeft PGGM's domeinsplitsing.** APG toont hoe locatiepagina's aggregators verslaan. a.s.r. en Achmea tonen hoe vakgebiedpagina's op head terms kunnen ranken.

Aandachtspunt: MN Pensioenbeheer is in 2026 in PGGM opgegaan (260 medewerkers), maar `werkenbijmn.nl` staat nog volledig overeind als zelfstandige carrièresite. Twee werkgeversmerken die om dezelfde kandidaten concurreren.

---

## 3. Aanbevolen aanpak

### Eerst verifiëren (één crawl, ongeveer een uur)

Dit beslecht de vragen die deze check open moest laten en bepaalt de zwaarte van bijna alles hierboven:

1. HTTP-statuscodes en redirects op beide domeinen
2. `rel=canonical` — staat die er, en in welke richting?
3. `JobPosting`-markup en de Search Console-rapportage "Vacatures" op beide hostnames
4. `robots.txt`, XML-sitemaps, `hreflang` — inclusief het AI-crawlerbeleid (worden GPTBot en ClaudeBot geweerd? dat zou de dominantie van derden mede verklaren)
5. Staan er wél vacature-detailpagina's op werkenbijpggm.nl? (zie de gemelde tegenstrijdigheid)
6. Backlinkvergelijking tussen beide domeinen in Ahrefs of Semrush

### Prioriteit 1 — structureel

**A. Kies één canoniek carrièredomein en 301-redirect de ander.** Twee geïndexeerde kopieën laten bestaan is de slechtste van alle opties: je betaalt de kosten van beide en oogst de voordelen van geen van beide.

*Scenario A — consolideren op `pggm.nl/werken-bij` (laagste risico):* sluit aan bij de feitelijke situatie (pggm.nl wint 13/14, bezit de vacature-laag, de Engelse laag, sollicitatieprocedure en contact), profiteert van de volledige corporate autoriteit, geen migratie van de converterende laag nodig. `werkenbijpggm.nl` blijft bestaan als vanity-redirect voor campagnes, print en social. Nadeel: het employer-brandmerk bouwt zelf nooit autoriteit op en blijft afhankelijk van de corporate release-cyclus.

*Scenario B — consolideren op `werkenbijpggm.nl` (strategisch sterker, duurder):* in lijn met MN, Achmea en a.s.r.; eigen tone of voice, eigen releasetempo, heldere meetbaarheid, en het domein zegt wat het is. Nadeel: je verplaatst de winnende kant naar de verliezende kant. Alle 13 winnende posities moeten opnieuw worden verdiend, de hele vacature- en Engelse laag moet mee, en je moet een dip van maanden accepteren in een markt waar circa 250 vacatures per jaar gevuld moeten worden. Alleen verdedigbaar met eigen budget, eigen team en een horizon van 12-18 maanden.

Let op bij beide: een cross-domain canonical is géén volwaardig alternatief voor een 301 — Google behandelt die als hint, en de slug- en titelverschillen maken het aannemelijk dat de hint genegeerd wordt. Redirect per URL naar het inhoudelijke equivalent, nooit in bulk naar de homepage, en controleer de afwijkende slugs handmatig.

**B. Ruim de andere twee hostnames op.** `pggm.onlinevacatures.nl` uit de index (robots + noindex, of canonical naar de eigen vacaturepagina); `pggm-prod65.adobecqms.net` blokkeren.

### Prioriteit 2 — snel en goedkoop

3. **Functieslugs in alle vacature-URL's** op het gekozen domein. Directe, goedkope oorzaak van de zwakke posities op functiequeries.
4. **Verlopen vacatures op 410 of 301** naar het vakgebiedoverzicht; `validThrough` correct zetten. Nu landt een kandidaat op de sterkste functiequery op een doodlopende pagina.
5. **Legacy `.aspx`-URL's redirecten** naar hun actuele equivalent — de FAQ verslaat nu de echte sollicitatieprocedurepagina.
6. **Parameterruis opruimen:** `?amp=`-varianten, facetten en paginering op noindex of canonical naar de schone URL.
7. **Functietitels herschrijven** naar zoektermen: uren, locatie, afdelingscodes en interne merken (StiPP, "3D", "IM IT") uit het titelveld.
8. **Titles herschrijven** volgens het APG-model: vraaggericht, met functie- of locatieterm, binnen normale lengte, één keer branding. Niet het a.s.r.-model kopiëren (titles van 150+ tekens vol herhaalde plaatsnamen).
9. **Eén cijferbron vastleggen** (jaarverslag 2025) met een definitie per getal en een jaarlijks updatemoment, en elke vindplaats bijwerken. Overweeg afgeronde formuleringen ("bijna 2.000 collega's") die minder snel verouderen.

### Prioriteit 3 — content die het gat met derden dicht

10. **Salarisranges per functiefamilie in HTML**, en `baseSalary` in `JobPosting`-schema. Dit verdringt Indeed en Glassdoor als bron, sluit aan bij de eigen waarde "vertrouwen", en loopt vooruit op de EU-loontransparantierichtlijn (informatieplicht vóór het gesprek vanaf 7 juni 2026).
11. **Een echte FAQ met `FAQPage`-schema:** doorlooptijd, gespreksrondes, wat het assessment inhoudt, screening, contact met recruiters. Elk antwoord als zelfstandig citeerbare alinea van 40-60 woorden — zo werken answer engines.
12. **Verhalenhub uit de 800 best stories.** Het materiaal bestaat al en het is authentiek opgehaald. Filterbaar op vakgebied en op waarde, eigen URL per verhaal, met naam, functie, afdeling en dienstjaren. Adresseer expliciet het terugkerende "het verschilt sterk per afdeling" uit de reviews.
13. **Locatiepagina's** voor Zeist en regio Utrecht (en Den Haag, gezien de MN-integratie). APG bewijst dat dit werkt.
14. **Vakgebiedpagina's van beschrijvend naar wervend** — en op head terms laten ranken. Begin bij vermogensbeheer/asset management: daar is PGGM nu onvindbaar terwijl het de kern van de organisatie is.
15. **Eén pagina "Zo werken wij hybride"**: hoeveel dagen op kantoor, hoe afspraken tot stand komen, plus de bestaande vergoedingen. Meest gestelde vraag, antwoord ontbreekt.
16. **Eén `Organization`-entiteitsblok** met identieke formulering op elke carrièrepagina en in schema, inclusief `sameAs` naar Wikipedia NL, LinkedIn, X en Instagram. Werk het Nederlandse Wikipedia-lemma bij met correcte kerncijfers; maak Engelstalige kernwerkgeverscontent zodat Engelse AI-antwoorden niet op het PFZW-lemma terugvallen.
17. **Het Grand Café centraal zetten:** eigen pagina met boekingsmogelijkheid, op elke vacature en elke vakgebiedpagina, plus korte video's. Dit is het sterkste onderscheid dat PGGM heeft.
18. **Maak van de MN-integratie een SEO-beslissing**, niet alleen een HR-beslissing: `werkenbijmn.nl` concurreert nu met het eigen merk.

---

## 4. Openstaande vragen

- Staan er canonicals tussen beide domeinen, en in welke richting?
- Is er `JobPosting`-markup, en staan de vacatures in Google for Jobs?
- Worden AI-crawlers geweerd in `robots.txt`?
- Zijn er vacature-detailpagina's op werkenbijpggm.nl geïndexeerd? (agents spraken elkaar tegen)
- Welke URL gebruikt PGGM zelf in LinkedIn-posts en vacatureplaatsingen? (`#werkenbijpggm` is een hashtag — waar wijzen de links heen?)
- Staan de genoemde cijfers vandaag nog letterlijk op de pagina's, of zijn de snippets verouderd?
- Core Web Vitals, toegankelijkheid en mobiel gedrag: volledig buiten bereik van deze methode.

---

## 5. Methode

Zes parallelle onderzoeksagents, elk met een eigen onderzoeksvraag en eigen zoekopdrachten:

| Agent | Focus | Zoekopdrachten |
|---|---|---|
| 1 | Indexatie en sitestructuur | 10 |
| 2 | Vacature-vindbaarheid en Google for Jobs | 17 |
| 3 | GEO/AEO en AI-zichtbaarheid | 12 |
| 4 | Domeinstrategie pggm.nl versus werkenbijpggm.nl | 14 |
| 5 | Employer brand en content | 12 |
| 6 | Concurrentiebenchmark | 14 |

Bevindingen die door meerdere agents onafhankelijk zijn gevonden (de domeinsplitsing, de cijferinconsistentie, de dominantie van aggregators) wegen in dit rapport zwaarder dan losse waarnemingen. Waar agents elkaar tegenspreken, staat dat er expliciet bij.
