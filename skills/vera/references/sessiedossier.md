# Model voor het sessiedossier en het startblok

Hoort bij werkproces D van de skill `vera`. Lees dit voordat je een sessiedossier aanmaakt of
bijwerkt, en voordat je een startblok levert.

## 1. Het sessiedossier

Eén document per project in de Drive-map `EQwise/Secretariaat/Sessies`, titel
`<jjjj-mm-dd> <project> sessie`. De datum is die van de laatste bijwerking, dus je hernoemt het
document als je het bijwerkt. Eén A4, de stand van nu, geen geschiedenis.

```markdown
# <project> sessie

Klant of project: <naam>
Laatst bijgewerkt: <jjjj-mm-dd>
Status: loopt | wacht op besluit | wacht op klant | stil

## Waar het over gaat
Eén alinea van maximaal vier regels: wat wordt er gemaakt of opgelost, en waarom.

## Stand van zaken
- <wat af is, per regel, maximaal vijf regels>

## Waar we gebleven zijn
Eén alinea: de laatste handeling die is uitgevoerd, en waarom het daar is gestopt.

## Open besluiten
- <Besluit uit de takenlijst, met de opties en de datum waarop het is vastgelegd>
- <of: geen>

## Eerstvolgende stap
Eén regel, één concrete handeling. Niet een doel, maar de eerste handeling.

## Materiaal en links
- Site of staging: <url of ONBEKEND>
- Map in Drive: <link of ONBEKEND>
- Verslag of dossier: <link of ONBEKEND>
- Betrokken skill of agent: <naam>

## Startprompt
<het startblok uit deel 2 hieronder, letterlijk>
```

Bijwerken doe je op drie momenten: als er een besluit open komt te staan, als een deelstap af is, en
als de sessie stopt. Wat afgerond is haal je uit Stand van zaken zodra het in de taken of in een
verslag staat, zodat het dossier kort blijft.

## 2. Het startblok

Dit blok kan Martin ongewijzigd plakken in een nieuwe sessie. Je levert het in een codeblok, zodat
kopiëren in één keer gaat. Wat je niet weet zet je op `ONBEKEND`, je vult nooit een aanname in.

```text
Start <skill of agent> voor <klant of project>.

Context:      <waar het over gaat, twee regels>
Materiaal:    <urls en mappen, per regel één>
Al gedaan:    <maximaal drie regels>
Gestopt bij:  <de laatste handeling en waarom het daar stopte>
Besluiten:    <genomen besluit en het antwoord, of: nog open, zie hieronder>
Open vragen:  <de besluiten die nog op Martin wachten, of: geen>
Eerste stap:  <één concrete handeling>
Let op:       <valkuil of afspraak die eerder is gemaakt, of: niets>
```

Regels bij het startblok:

1. De eerste regel noemt altijd de skill of de agent die moet starten, zodat de volgende sessie
   meteen in de juiste modus begint.
2. Bij Eerste stap staat een handeling, geen doel. Dus niet "de pagina afmaken" maar "sectie
   Diensten in Divi 5 op de staging bouwen volgens het paginaplan".
3. Staan er open besluiten, dan zet je die letterlijk in het blok, met de opties. Zo kan Martin bij
   het starten in één keer beslissen.
4. Heeft Martin een besluit inmiddels genomen, dan staat het antwoord bij Besluiten en niet meer bij
   Open vragen, en je zet de rij in Taken op `afgerond`.

## 3. Wegschrijven van een besluit

Regel voor het tabblad Taken, via de verzendbrug uit deel 8 van de skill:

```bash
curl -sL -X POST "$SECRETARIAAT_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "sleutel": "'"$SECRETARIAAT_SLEUTEL"'",
    "actie": "rijen",
    "tabblad": "Taken",
    "rijen": [
      {"Taak": "Besluit: welke hero-variant voor OmniHealth",
       "Klant of project": "OmniHealth",
       "Deadline": "2026-09-15",
       "Prioriteit": "hoog",
       "Status": "open",
       "Bron": "sessie OmniHealth Divi 5 2026-09-11",
       "Notitie": "Opties: A rustige hero met foto | B hero met bewegende cijfers; Advies: A, past beter bij de doelgroep; Gevolg zonder besluit: de homepage blijft onaf; Hervat met: 2026-09-11 OmniHealth sessie"}
    ]
  }'
```

Beslist Martin, dan zet je de rij om. De statusactie raakt alleen de kolom Status, de brug kan geen
bestaande cel overschrijven, dus het antwoord zelf leg je vast in het sessiedossier onder Open
besluiten:

```bash
curl -sL -X POST "$SECRETARIAAT_URL" \
  -H 'Content-Type: application/json' \
  -d '{"sleutel": "'"$SECRETARIAAT_SLEUTEL"'", "actie": "status",
       "tabblad": "Taken", "id": "T-0042", "status": "afgerond"}'
```

Ligt de brug eruit, dan lever je de rij als tab-gescheiden regel in de chat, zodat Martin hem zelf
kan plakken. Een besluit blijft nooit onvastgelegd omdat de techniek hapert.

## 4. Het verbruiklogboek

Hoort bij werkproces E. Eén document in Drive, `EQwise/Secretariaat/Verbruik`, tenzij er een tabblad
Verbruik in de sheet staat. Nieuwste meting bovenaan.

```markdown
# Verbruik Claude

Abonnement: <naam of ONBEKEND>
Vensters: sessievenster rolt vanaf het eerste bericht, weekvenster reset <dag en tijd, of ONBEKEND>

| Tijd | Sessie | Week | Reset sessie | Reset week | Model | Wat liep er | Bron |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-12 09:10 | 18% | 64% | 13:40 | zo 03:00 | opus | dagstart | /usage |
```

In de kolom Bron staat waar het getal vandaan komt: `/usage`, `instellingen`, of `plak van Martin`.
Een regel zonder bron schrijf je niet weg.

Bij het advies noem je altijd het tijdstip van de meting, dus "week stond om 09:10 op 64 procent",
nooit "de week zit op 64 procent" alsof het nu gemeten is.
