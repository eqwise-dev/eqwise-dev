# EQwise werkafspraken voor Claude

## SEO-checks

- Doe elke SEO-check (site-audit, rankings, zoekwoorden, backlinks, concurrenten) via het EQwise-account op WebCEO (webceo.com).
- De login loopt via de MCP-connector "EQwise SEO-platform" (tools `mcp__EQwise_SEO-platform__*`), die de WebCEO-API aanspreekt via seo.eqwise.nl. Begin met `list_projects`.
- Is WebCEO niet bereikbaar? Meld dat dan, noem de foutmelding en gebruik GTmetrix (gtmetrix.com) als alternatief, in elk geval voor snelheid en Core Web Vitals.
- Stap niet ongemerkt over op andere bronnen (Ahrefs, Firecrawl, PageSpeed). Gebruik je ze toch als aanvulling, zeg dan per cijfer uit welke bron het komt.
- Noem bij een positie altijd de zoekmachine, het land, de taal, het apparaat en de locatie.
- Noem bij zoekvolume altijd de scope: globaal of een land.
- Gebruik in rapporten voor klanten de naam "het EQwise SEO-platform" en noem geen leverancier.

## SEO- en GEO-rapporten

- Elk SEO- en GEO-rapport voor een klant krijgt de vaste EQwise-rapportstijl: de huisstijl van eqwise.nl in het design van de kennisbankblog (oktober 2026).
- Lees eerst `rapporten/README.md` en begin met een kopie van `rapporten/voorbeeld/audit-opruimbrigade-2026-10-18.html`. Bouw geen eigen opmaak.
- Gebruik het logo uit `rapporten/logo/`, inline als SVG.
- Controleer voor oplevering met `rapporten/scripts/rapport-qa.js` en lever HTML en A4-PDF.
- Loop vóór oplevering de "Lessen uit eerdere rapporten" en "Vaste woorden" in `rapporten/README.md` na. Krijg je feedback van Martin op een rapport, zet de les daar erbij.
