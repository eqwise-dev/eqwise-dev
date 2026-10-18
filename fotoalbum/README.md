# Fotoalbum: één bron, print én web

`build.py` maakt van één `album.json` twee uitvoeren:

| Uitvoer | Map | Inhoud |
|---|---|---|
| Print | `uitvoer/print/` | `album-binnenwerk.pdf`: losse pagina's met afloop voor Blurb "PDF to Book", plus `proef.png` met snij- (rood) en veiligheidslijnen (blauw) |
| Web | `uitvoer/web/` | `index.html` als preview en `album-fragment.html` om op de website te plaatsen; WebP in 640/1280/1920 px, alt-teksten, `ImageGallery`-schema |

## Gebruik

```bash
pip install pillow pypdf numpy
python3 fotoalbum/testfotos.py                                  # alleen voor het voorbeeld
python3 fotoalbum/build.py fotoalbum/voorbeeld/album.json --proef
```

Een PDF maken vraagt Chrome of Chromium. Foto's horen in de map `fotos/` naast `album.json`.

## Formaat

Standaard staat Blurb Large Landscape ingesteld: 13 × 11 inch (33 × 28 cm), liggend, 0,125 inch afloop rondom, dus 13,25 × 11,25 inch per PDF-pagina.
**Controleer dat in Blurbs Specification Calculator** voor de gekozen kaft en het aantal pagina's, en zet daarna `"maat_gecontroleerd": true`. De kaft is een aparte PDF; de rugdikte hangt af van het aantal pagina's.

## album.json

- `hoofdstukken[].paginas[].layout`: `vol`, `duo`, `drie`, `vier`, `passe-partout` of `panorama` (loopt over twee pagina's en begint altijd links).
- Per foto: `bestand`, `alt` (web en SEO), optioneel `focus` (bijvoorbeeld `"30% 50%"` om het onderwerp in beeld te houden) en `alleen_print: true` voor foto's die niet online mogen (AVG).
- Per pagina een optioneel `bijschrift`, dat in het boek en op de webpagina verschijnt.

## Helderheid en kleur op elkaar afstemmen

Standaard brengt het script alle foto's licht in lijn met je **bewerkte** foto's: bestanden in `fotos/bewerkt/` of foto's met `"bewerkt": true`. Bewerkte foto's zelf blijven ongemoeid.

- Helderheid: de mediaan schuift richting die van de bewerkte foto's, met hoogstens ongeveer een halve stop.
- Kleurzweem: wordt gemeten op bijna-neutrale vlakken (grijs, wit, bewolkte lucht) en gecorrigeerd met hoogstens 6% per kleurkanaal. Verzadigde kleuren, zoals de vogel zelf of een blauwe lucht, tellen bij het meten niet mee.
- Instellen met `"harmoniseren": {"aan": true, "sterkte": 0.6}`. Een sterkte van 0 doet niets, 1 is de volle correctie (binnen de grenzen). Per foto zet je het uit met `"harmoniseren": false`.
- Met `--proef` maakt het script ook `harmonisatie.jpg` met elke gecorrigeerde foto voor en na. De console toont per foto wat er veranderde, bijvoorbeeld `+0.3 stop, warmer`.

De correctie geldt voor print en web, zodat beide er hetzelfde uitzien. Print krijgt daarbovenop de vaste extra helderheid (`print_helderheid`).

## Wat het script bewaakt

- **Resolutie per vak:** onder 200 dpi volgt een waarschuwing "TE KLEIN", onder 240 dpi "MATIG".
- **Foto's goed gedraaid:** op basis van EXIF, en omgezet naar sRGB. Voor print worden ze iets lichter gemaakt (`print_helderheid`).
- **Privacy:** webbeelden worden opnieuw opgeslagen zonder EXIF, dus zonder GPS-locatie.
- **Paginamaat en aantal pagina's:** de PDF wordt nagemeten; het aantal pagina's is altijd even en komt minimaal op `min_paginas`.

## Het hele systeem (swarm)

Twee workflows in `.claude/workflows/` sturen meerdere agents aan. Daartussen keurt de fotograaf twee keer goed.

| Stap | Wie | Hoe |
|---|---|---|
| 1. Selectie | workflow `fotoalbum-selectie` | `selectie.py` groepeert bursts en meet de scherpte. Curator-agents (maximaal 4 parallel) beoordelen elk moment op contactvel en 100%-uitsnede: oog scherp, vogel heel, albumwaardig. Per batch bepaalt een tweede agent blind de vogelsoort; alleen bij overeenstemming geldt een soort als "zeker". |
| 2. Goedkeuren | fotograaf | `uitvoer/selectie/curatie.html`: beslispunten staan bovenaan |
| 3. Bouwen | workflow `fotoalbum-bouw` | De art director maakt verhaal en layout en schrijft `album.json`. Daarna volgen teksten per hoofdstuk (parallel), dan build, ON1 en opnieuw build, dan print- en webcontrole (parallel) en één herstelronde. |
| 4. Eindcontrole | fotograaf | `uitvoer/print/proef.png` en `harmonisatie.jpg` |
| 5. Publiceren | fotograaf / Claude | De PDF upload je zelf naar Blurb; de webpagina komt als concept op de site |

Starten in Claude Code, in deze repository, op de Mac met ON1:

```
voer workflow fotoalbum-selectie uit met fotomap ~/Pictures/vogelalbum/fotos
voer workflow fotoalbum-bouw uit met album ~/Pictures/vogelalbum/album.json en curatie ~/Pictures/vogelalbum/uitvoer/selectie/curatie.json
```

Losse stappen kunnen ook zonder agents:

```bash
python3 fotoalbum/selectie.py ~/Pictures/vogelalbum/fotos           # bursts en scherpte
python3 fotoalbum/build.py ~/Pictures/vogelalbum/album.json --proef
python3 fotoalbum/on1_brug.py stuur ~/Pictures/vogelalbum/album.json
python3 fotoalbum/on1_brug.py haal  ~/Pictures/vogelalbum/album.json
```

## ON1 eenmalig inrichten

ON1 Photo RAW heeft geen API of opdrachtregel. De brug loopt via **Folder Actions**.

1. Maak een preset "Album: NoNoise + Resize 2x" met NoNoise AI aan, en voeg Resize AI 200% toe als je versie dat in een preset of export toestaat.
2. Maak een Folder Action op de map uit `album.json` → `"on1": {"in": ...}`. Die past de preset toe en exporteert naar `"uit"`: originele grootte, JPG 95 of meer (of TIFF), sRGB, zonder exportverscherping.
3. Laat ON1 open staan tijdens `fotoalbum-bouw`. `on1_brug.py haal` wacht tot 30 minuten en zet de resultaten in `fotos/verbeterd/`. `build.py` gebruikt die automatisch.

Of Resize AI in een Folder Action meegaat, hangt af van je ON1-versie; dat test je met 3 tot 4 foto's.

## Kaartjes, plaatsnamen en typografie

- **GPS uit EXIF:** per hoofdstuk worden de opnamepunten verzameld. Via OpenStreetMap komen daar plaats, provincie, land en het **natuurgebied** bij (nationaal park, beschermd gebied of natuurreservaat), met de contour van het park. Alles wordt bewaard in `plaatsen-cache.json` naast `album.json`, zodat elk punt maar één keer wordt opgevraagd. Zonder GPS of internet zet je per hoofdstuk zelf `"plek"`, `"gps": [lat, lon]` en/of `"periode"`. Met `"plaatsen": {"online": false}` vraagt het script niets op.
- **Kaarten** zijn vectorgraphics (SVG), dus haarscherp in de PDF. Er zijn drie soorten:
  - een overzichtskaart met genummerde hoofdstukken (pagina 2);
  - een grote kaart links naast een hoofdstukopening die anders op een linkerpagina zou vallen;
  - een klein kaartje op de opening zelf: ingezoomd op het park, met het land als inzetkaartje.

  De randen lopen zacht weg in het papier.
- **Hoofdstukopening:** een kicker ("Hoofdstuk 02"), de titel in Cormorant Garamond, een dunne lijn, de plek in spatieerde kapitalen, coördinaten en periode cursief, en daaronder de intro.
- **Lettertypen:** Cormorant Garamond (SIL Open Font License, zie `fonts/OFL-CormorantGaramond.txt`) voor koppen en tekst, Inter voor kleine labels. Voor het web wordt het lettertype automatisch verkleind tot WOFF2 met alleen de Latijnse tekens (`pip install fonttools brotli`).
- **Bronvermelding:** "Natural Earth, © OpenStreetMap-bijdragers" staat op de overzichtspagina en onder de webpagina. De ODbL-licentie van OpenStreetMap vraagt dat.
- **Basiskaart:** Natural Earth 1:50m (`kaartdata/landen.geojson`, publiek domein). Ingezoomd op een klein park is de kustlijn daarvan grof; de parkcontour zelf komt uit OpenStreetMap en is wel precies.

## Lijniconen

Een kleine set dunne lijniconen (`fotoalbum/iconen.py`, vector, in de accentkleur) begeleidt de tekst. Ze worden bewust spaarzaam ingezet:

- **Titelpagina:** een veer boven de titel.
- **Hoofdstukopening:** één leefgebied-icoon boven "Hoofdstuk 01". Het script kiest dat op trefwoorden in titel, intro en plek: kust, duin, water/riet, heide, bos, berg, savanne/wildpark, sneeuw/ijs, en anders een veer. Overschrijven doe je met `"icoon": "heide"`, uitzetten met `"icoon": "geen"`.
- **Coördinatenregel:** een klein kompas.
- **Overzichtspagina:** het leefgebied-icoon naast elk hoofdstuk.

Bij de foto's zelf staan geen iconen, zodat het beeld rustig blijft.

## Kaft

`build.py` maakt naast het binnenwerk ook `album-kaft.pdf`: één doorlopende omslag voor Blurb ImageWrap, met achterkant, rug, voorkant en de omslagrand rondom. Met `--proef` volgt `kaft-proef.png` met hulplijnen: rood is de snijrand, oranje de rug, blauw gestippeld de veilige zone (weg van snijrand en scharnier).

```json
"kaft": {
  "stijl": "beeld",                 // of "passe-partout"
  "voor": "bewerkt/ijsvogel.jpg",   // standaard: de eerste volle pagina uit het album
  "voor_focus": "60% 45%",
  "achtertekst": "Eén of twee zinnen voor de achterkant.",
  "kaart_achter": true,
  "rug_richting": "omhoog",         // omhoog = Europees, omlaag = Engels/Amerikaans
  "paneel_breedte_in": 13.25, "paneel_hoogte_in": 11.25, "omslag_in": 0.75,
  "scharnier_in": 0.4, "rug_in": 0.36,
  "maat_gecontroleerd": true
}
```

- **beeld:** de voorkant is volledig gevuld met de sterkste foto, met de titel klein en wit op een zacht verloop.
- **passe-partout:** papierkleur, met één foto in een ruime marge en de titel eronder. Dat is de klassieke fine-art-kaft.
- **Achterkant:** de korte tekst en de overzichtskaart met genummerde plekken, verder niets.
- **Rug:** de titel en je naam als één gedraaide regel.

**De maten zijn een schatting** totdat je de waarden uit Blurbs Specification Calculator invult. De rugdikte hangt af van het aantal pagina's en het papier. Zolang `maat_gecontroleerd` niet `true` is, geeft de build een duidelijke waarschuwing.

## Reizen en safari (bijvoorbeeld Tanzania)

- **Meren op de kaart:** Natural Earth-meren (`kaartdata/meren.geojson`), zodat het Victoria-, Tanganyika- en Malawimeer als water te zien zijn en niet als land.
- **Parken en leefgebieden** worden herkend voor het icoon: Serengeti, Ngorongoro, Tarangire, Manyara, Ruaha, Nyerere/Selous en Mikumi worden savanne; Kilimanjaro en Meru worden berg; Zanzibar en Pemba worden kust; Natron en Eyasi worden water.
- **Camera zonder GPS:** zet telefoonfoto's van dezelfde reis in `fotos/telefoon/`. Een hoofdstuk zonder GPS leent dan de locaties van telefoonfoto's die binnen een uur van de eigen opnames zijn gemaakt. Staat de cameraklok niet op lokale tijd, zet dan `"plaatsen": {"camera_tijdverschil_min": 60}` (minuten die bij de cameratijd worden opgeteld; Nederlandse zomertijd naar Tanzania is +60).
- **Land:** komt uit OpenStreetMap, anders uit `"land"` in `album.json`, en anders uit de kaart zelf.
- **Soorten:** de selectie-swarm determineert vogels én zoogdieren, met Nederlandse en wetenschappelijke naam. De twee determinaties gelden als eens als een van beide namen overeenkomt.

## Luchtbeelden (Google Earth Pro)

Per hoofdstuk kan een luchtbeeld als paginavullende pagina naast de opening staan:

```json
{ "titel": "In de krater", "luchtfoto": "luchtbeelden/ngorongoro.jpg",
  "luchtfoto_bron": "Beeld: Google Earth · © 2026 Airbus", "luchtfoto_focus": "50% 45%" }
```

- **Exporteren:** in Google Earth Pro via *Bestand → Afbeelding opslaan*, op de hoogste resolutie. Volgens oudere bronnen is dat maximaal ongeveer 4800 × 3200 px; controleer het in je eigen versie. Dat is genoeg voor één volle pagina (ongeveer 360 dpi), niet voor een hele spread.
- **Plaatsing:** valt de opening rechts met een vrije linkerpagina ervoor, dan komt het luchtbeeld links (een mooie spread). Anders komt het direct na de opening.
- **Regels van Google (geo-richtlijnen):** boeken tot 5.000 exemplaren zijn toegestaan, maar alleen met een leesbare bronvermelding van minstens 6 pt en zonder commercieel of promotioneel gebruik. Het script:
  - laat het beeld ongemoeid: geen kleurafstemming, geen extra helderheid, niet naar ON1;
  - zet `luchtfoto_bron` altijd zichtbaar op de pagina. Neem daarin de dataleveranciers over die Google Earth onderin het beeld toont;
  - zet een handelsmerk- en non-affiliatieregel op de overzichtspagina;
  - laat luchtbeelden **weg uit de webversie**, tenzij je `"luchtfoto_web": true` zet. Een bedrijfswebsite telt al snel als promotioneel gebruik.

Controleer de actuele richtlijnen op about.google voordat je drukt.
