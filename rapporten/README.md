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
| 5 | Zijkolom | sticky "In dit rapport" met actieve markering, daaronder het telefoonnummer. Verdwijnt onder 1100 px |
| 6 | Opgesteld door | naam, rol, datum en bronnen van de meting |
| 7 | Blauwe band | één zin in Poppins met het tweede deel vet, een korte toelichting, witte knop |
| 8 | Voet | logo, adres Laan van Kronenburg 14, 1183 AS Amstelveen, +31 20 893 20 84, KvK 34191949 |

Vaste hoofdstukken voor een audit, in deze volgorde: Stand, Meting, Acties, Bewijs, Fixes,
Sterk, Vervolg. Laat een hoofdstuk weg als er niets in staat; verzin geen vulling.

## Componenten

- **Figuurvlak** (`.figuur`): lichte achtergrond `--vlak`, radius 16, titel in Poppins 600. Voor
  cijfers, tegels en codeblokken. Een bijschrift zegt wat het cijfer betekent.
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
Kolom 1200 px, kantlijn 168 px, zijkolom 248 px. Donkere modus en printversie zitten in de CSS.

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

## Oplevering

1. Draai `node rapporten/scripts/rapport-qa.js <rapport.html> <uitmap>`. Elke regel moet `ok`
   zijn op 320, 375, 390, 430, 768, 1024, 1280, 1440 en 1920, licht en donker.
2. Bekijk de schermafdrukken van 1440 en 390 en de PDF op overlap bij paginaovergangen.
3. Lever de HTML en de A4-PDF op.
