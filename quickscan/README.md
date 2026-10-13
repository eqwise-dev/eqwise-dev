# EAA-quickscan: rapportsjabloon

Sjabloon voor het EQwise-quickscanrapport over digitale toegankelijkheid
(WCAG 2.2 AA / European Accessibility Act). Per klant vul je één JSON-bestand;
het script maakt daar een rapport van 6 pagina's van in de EQwise-huisstijl, als HTML en PDF.

Bekijk `voorbeeld-rapport.pdf` voor het resultaat met fictieve gegevens.

## Bestanden

| Bestand | Wat |
|---|---|
| `template.html` | Het sjabloon (Jinja2), A4 en printklaar |
| `voorbeeld.json` | Ingevuld voorbeeld met alle velden |
| `render.py` | Maakt van een JSON-bestand een HTML- en PDF-rapport |
| `voorbeeld-rapport.pdf` | Het voorbeeld als PDF |

## Gebruik

```bash
pip install -r ../requirements.txt
cp voorbeeld.json rapporten/klantnaam.json   # invullen
python render.py rapporten/klantnaam.json --pdf
```

De map `rapporten/` staat in `.gitignore`: klantgegevens komen niet in git.

Voor de PDF zoekt het script Chrome of Chromium. Wordt die niet gevonden, zet dan
`CHROME_PATH`, of open de HTML in Chrome en kies **Afdrukken > Opslaan als PDF**
(marges: standaard, kop- en voetteksten uit).

Het script controleert vooraf of alle verplichte velden er zijn, of de keuzewaarden
kloppen en of er handmatige controles zijn ingevuld. Bevindingen worden automatisch
op ernst gesorteerd.

## Opbouw van het rapport

1. **Voorblad** met de gegevens van de klant en de verantwoording (wat een quickscan wel en niet is)
2. **Samenvatting**: oordeel, kerncijfers, valt de klant onder de EAA, wat is onderzocht
3. **De belangrijkste drempels**: maximaal 5, elk met WCAG-criterium, wie er last van heeft, oplossing, inspanning en effect op SEO/GEO
4. **Overzicht** per WCAG-principe en de handmatige controles
5. **Toegankelijk én beter vindbaar**: de SEO/GEO-koppeling
6. **Volgende stappen**: van gesprek naar herstel, keurmerk en abonnement

## Keuzewaarden

| Veld | Toegestane waarden |
|---|---|
| `eaa.valt_onder` | `ja`, `waarschijnlijk`, `nee`, `onbekend` |
| `oordeel.niveau` | `rood` (veel drempels), `oranje` (enkele drempels), `groen` (goed op weg) |
| `bevindingen[].ernst` | `hoog`, `middel`, `laag` |
| `bevindingen[].inspanning` | `klein` (uren), `middel` (dagen), `groot` (weken) |
| `principes[].status` | `rood`, `oranje`, `groen` |
| `handmatige_checks[].resultaat` | `voldoet`, `deels`, `voldoet niet` |

`bevindingen[].seo_geo` mag `null` zijn; dan valt het blok weg.

`bevindingen[].wcag` mag een lege lijst zijn als een bevinding niet onder één WCAG-criterium valt (bijvoorbeeld een ontbrekende toegankelijkheidsverklaring). Zet dan in `bevindingen[].grondslag` waar de eis vandaan komt.

## Werkwijze per scan

1. **Automatisch**: scan de 3 tot 5 belangrijkste pagina's (homepage plus de kerntaak, zoals product → winkelwagen → afrekenen) met axe-core of Lighthouse.
2. **AI-analyse**: laat de AI-bot de scanresultaten, broncode en schermafbeeldingen omzetten naar `klant.json` (zie de prompt hieronder).
3. **Handmatig, verplicht**: doe minimaal deze controles zelf en vul `handmatige_checks` in:
   - de volledige kerntaak uitvoeren met alleen het toetsenbord
   - focus is altijd zichtbaar
   - skiplink naar de hoofdinhoud
   - koppenstructuur en formulier met een schermlezer (NVDA of VoiceOver)
   - inzoomen tot 200% en een smal scherm van 320 pixels
4. **Controleer elke bevinding** van de AI op de echte pagina. Een onjuiste bevinding kost je geloofwaardigheid.
5. **Render** het rapport en lees de PDF één keer helemaal door voordat je hem verstuurt.

## Prompt voor de AI-bot

```
Je bent toegankelijkheidsspecialist bij EQwise. Zet de onderstaande scanresultaten
om naar JSON volgens exact dezelfde structuur als voorbeeld.json.

Regels:
- Kies maximaal 5 bevindingen: de drempels die bezoekers het meest hinderen,
  met de afrondtaak (bijv. afrekenen) voorop.
- Noem per bevinding de juiste WCAG 2.2-succescriteria met nummer, Nederlandse
  naam en niveau.
- Schrijf in gewone taal voor een directeur of marketeer, niet voor een developer.
  Geen jargon zonder uitleg. Spreek de lezer aan met "u".
- "wat_we_zagen" beschrijft alleen wat aantoonbaar in de scan staat. Verzin niets.
- Vul "handmatige_checks" NIET in; dat doet een mens.
- Noem het nooit een audit of WCAG-EM-onderzoek; het is een quickscan.
- Geef alleen de JSON terug.

Scanresultaten:
[plak hier de axe-/Lighthouse-uitvoer, URL's en eventuele aantekeningen]
```

## Nog in te vullen

In `voorbeeld.json` staan `[e-mailadres]` en `[telefoonnummer]` bij `afzender`.
Vul die één keer in en gebruik dat bestand als basis voor elke nieuwe scan.
