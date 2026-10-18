# EQwise-rapporten: huisstijl en werkwijze

Vastgelegd op 18 oktober 2026, besluit Martin. Elk SEO- en GEO-rapport voor een klant
(audit, scan, maandrapport, GEO-meting) krijgt deze vormgeving. Het rapport leest als een
kennisbankartikel op eqwise.nl, in het design van de blogpagina's uit oktober 2026
(referentie: https://eqwise.nl/geo-optimalisatie/).

**Bron van waarheid:** `voorbeeld/audit-opruimbrigade-2026-10-18.html`. Begin elk nieuw
rapport met een kopie van dat bestand en vervang de inhoud. De CSS bovenin is het
volledige stijlsysteem; verander tokens daar en nergens anders.

## Opbouw van de pagina

| Volgorde | Onderdeel | Wat erin staat |
| --- | --- | --- |
| 1 | Topbalk | `Rapport voor <klant>` links, datum rechts, op `--vlak` |
| 2 | Kop | EQwise-logo (inline SVG), blauwe knop "Bespreek dit rapport" naar eqwise.nl/contact/ |
| 3 | Opening | kantlijn: label, auteur, datum, leestijd. Leeskolom: H1 met het domein in blauw, lead van 2 tot 4 zinnen, feitenregel (platform, hosting, wat gecontroleerd is). Rechts: meetkaart met het belangrijkste cijfer en de bron |
| 4 | Hoofdstukken | elk hoofdstuk is een `section.blok`: kantlijn met blauw streepje, label in hoofdletters en een korte noot; leeskolom met een H2 als vraag ("Hoe staat de site ervoor?") |
| 4a | Blauw blok | direct boven de actielijst: label "Actielijst in het kort", het aantal acties met het aantal hoog vet, de verdeling hoog/middel/laag in grote cijfers, en één zin waar je begint (uit de volgende stappen) |
| 5 | Zijkolom | sticky "In dit rapport" met actieve markering, daaronder het telefoonnummer. Verdwijnt onder 1100 px |
| 6 | Opgesteld door | naam, rol, datum en bronnen van de meting |
| 7 | Blauwe band | één zin in Poppins met het tweede deel vet, een korte toelichting, witte knop |
| 8 | Voet | logo, adres Laan van Kronenburg 14, 1183 AS Amstelveen, +31 20 893 20 84, KvK 34191949 |

Vaste hoofdstukken voor een audit, in deze volgorde: Stand, Meting, Acties, Bewijs, Fixes,
Sterk, Vervolg. Laat een hoofdstuk weg als er niets in staat; verzin geen vulling.

## Componenten

- **Figuurvlak** (`.figuur`): lichte achtergrond `--vlak`, radius 16, titel in Poppins 600. Voor
  cijfers, tegels en codeblokken. Een bijschrift zegt wat het cijfer betekent.
- **Blauw blok** (`.blauwblok`): volle `#3B3DFF`, witte tekst, radius 16, over kantlijn en
  leeskolom. Alleen boven de actielijst; de cijfers telt het bouwscript uit de acties.
- **Antwoordblok** (`.antwoord`): blauwe lijn links. Voor "Wat niet gemeten kon worden" en voor
  de kern van een hoofdstuk.
- **Tegels** (`.tegel`) met badge Goed, Matig of Zwak (`.b-ok`, `.b-mid`, `.b-hi`).
- **Cijfercellen** (`.cel`): groot getal in Poppins 700, kleur alleen voor goed, matig of slecht.
- **Staafjes** (`.staaf-rij`): zwart voor de referentie, blauw voor het onderwerp.
- **Actielijst** (`.actions .act`): rijen met een lijn, prioriteitsstreep links (hoog rood,
  middel amber, laag grijsblauw), filterchips per onderdeel, een "Fix"-regel per actie.
- **Tijdlijn** (`.tijdlijn`): genummerde blauwe stippen voor de volgende stappen.
- **Codeblok** (`.snip`) met knop Kopieer.

## Tokens

Kleuren van eqwise.nl: blauw `#3B3DFF`, diep `#2848A0`, donker `#16214A`, inkt `#111114`,
tekst `#3F4654`, mut `#4D5664`, lijn `#E3E8F2`, vlak `#F3F6FC`, zacht `#D8E2FF`,
grijsblauw `#B9C3DE`. Letters: Poppins 500/600/700 voor koppen en labels, Inter 400/500/600
voor tekst, IBM Plex Mono voor code. Spacing 4, 8, 12, 16, 24, 32, 48, 64, 80, 96, 128.
Kolom 1200 px, kantlijn 168 px, zijkolom 248 px. De printversie zit in de CSS.

**Altijd wit, net als eqwise.nl.** Geen donkere modus: het rapport zet `color-scheme: light`, ook als
het apparaat van de lezer op donker staat. De achtergrond is wit, met lichte vlakken (`--vlak`) voor
figuren. Blauw alleen als accent: labels, links, knoppen en de Q-staart, plus precies twee blauwe vlakken:
het blok boven de actielijst en de afsluitband.
Geen grote donkere of blauwe vlakken bovenaan.

## Logo

`logo/eqwise-logo.svg` gebruikt `currentColor` voor de letters; de Q-staart kleurt via
`.logo rect { fill: var(--blauw); }`. Plak de SVG inline, zodat het rapport één bestand blijft.
Let op: dit logo is nagebouwd uit Poppins Bold en vergeleken met het logo op eqwise.nl.
Vervang het door het originele bestand zodra dat er is (staat op de Mac mini).

## Inhoudsregels

- Noem bronnen in het rapport "het EQwise SEO-platform"; geen leveranciersnamen (zie CLAUDE.md).
- Bij een positie: zoekmachine, land, taal, apparaat en locatie. Bij zoekvolume: de scope.
- Wat niet gemeten is staat in "Wat niet gemeten kon worden", met de reden. Geen geschatte cijfers.
- Nieuwe tekst die niet uit de meting komt (knoppen, band, noten) meld je aan Martin bij de oplevering.

## Vaste woorden

| Gebruik | Niet |
| --- | --- |
| Van wie is het bedrijf (onderdeel, filter, labels) | Wie is het bedrijf |
| ... kunnen niet vaststellen van wie het bedrijf is | ... wie het bedrijf is |
| het EQwise SEO-platform | WebCEO, Ahrefs, Majestic, GTmetrix of een andere leverancier |

## Lessen uit eerdere rapporten

Fouten die Martin eerder moest terugsturen. Loop ze na vóór elke oplevering; de meeste vangt
`rapport-qa.js` automatisch af.

1. **Altijd wit.** Een donkere modus maakte het begin donker op een apparaat met donkere
   instelling. Geen `prefers-color-scheme: dark`, wel `color-scheme: light`.
2. **Blauw spaarzaam.** Precies twee blauwe vlakken: boven de actielijst en de afsluitband.
3. **Benaming.** "Van wie is het bedrijf", ook in de lopende tekst, niet alleen in kopjes en
   knoppen. Zoek na een hernoeming in de hele tekst, ook in lagere en hogere hoofdletters.
4. **Geen leveranciers.** "Ahrefs Brand Radar" en "Majestic" stonden in een eerste versie. In
   het rapport heet elke bron "het EQwise SEO-platform" of wordt beschreven zonder naam.
5. **Echt logo.** Geen wazige PNG en geen nagebootst woordmerk in gewone tekst. Inline SVG uit
   `logo/`.
6. **Tel uit de data.** Aantallen (acties, hoog/middel/laag) komen uit de lijst zelf, niet uit
   een losse telling. Een `grep -c` telde eerder ook CSS-regels mee.
7. **Geen onbewezen zinnen.** Zinnen als "het meeste werk per euro" of "Vertrouwelijk" zonder
   afspraak horen er niet in. Nieuwe tekst die niet uit de meting komt, noem je bij de oplevering.
8. **Ontbrekende meting melden, niet invullen.** Is een bron niet bereikbaar (bijvoorbeeld
   GTmetrix vanuit de cloudomgeving), zeg dat in "Wat niet gemeten kon worden" en aan Martin. Geen
   geschatte cijfers. Test de bereikbaarheid aan het begin, niet aan het eind.
9. **CSS die mobiel breekt.** Gebruik een klassenaam maar voor één ding (`.good` botste en gaf
   horizontale scroll). Grids met `minmax(min(100%, Xpx), 1fr)` en `min-width: 0` op grid-kinderen.
10. **Print.** Geen CSS-grid in de leeskolom bij print (gaf overlap op een paginaovergang) en
    geen `break-inside: avoid` op grote vlakken (gaf halflege pagina's).
11. **Nette HTML.** Eén `<!doctype>`, een echte `<head>` met `lang="nl"`, beschrijving en
    `noindex`. Geen dubbel geplakt documentskelet.

## Oplevering

1. Draai `node rapporten/scripts/rapport-qa.js <rapport.html> <uitmap>`. Elke regel moet `ok`
   zijn: eerst de inhoudscontroles (leveranciers, donkere modus, benaming, blauwe vlakken, logo,
   tellingen, placeholders), daarna 320, 375, 390, 430, 768, 1024, 1280, 1440 en 1920. Elke breedte
   draait ook met een donkere apparaatinstelling; het rapport moet dan nog steeds wit zijn.
2. Bekijk de schermafdrukken van 1440 en 390 en de PDF op overlap bij paginaovergangen. Schakel
   bij eigen schermafdrukken `scroll-behavior` uit, anders staat de pagina halverwege een scroll.
3. Lees de lopende tekst één keer helemaal door op de vaste woorden hierboven.
4. Lever de HTML en de A4-PDF op en noem nieuwe tekst die niet uit de meting komt.
5. Komt er een nieuwe fout uit Martins feedback, voeg hem toe aan "Lessen" en, als het kan, aan
   `rapport-qa.js`.
