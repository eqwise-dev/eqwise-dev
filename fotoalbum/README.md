# Fotoalbum: één bron, print én web

`build.py` maakt van één `album.json` twee uitvoeren:

| Uitvoer | Map | Inhoud |
|---|---|---|
| Print | `uitvoer/print/` | `album-binnenwerk.pdf`: losse pagina's met afloop voor Blurb "PDF to Book", plus `proef.png` met snij- (rood) en veiligheidslijnen (blauw) |
| Web | `uitvoer/web/` | `index.html` als preview en `album-fragment.html` om op de website te plaatsen; WebP in 640/1280/1920 px, alt-teksten, `ImageGallery`-schema |

## Gebruik

```bash
pip install pillow pypdf
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

## Wat het script bewaakt

- **Resolutie per vak:** onder 200 dpi volgt een waarschuwing "TE KLEIN", onder 240 dpi "MATIG".
- **Foto's goed gedraaid:** op basis van EXIF, en omgezet naar sRGB. Voor print worden ze iets lichter gemaakt (`print_helderheid`).
- **Privacy:** webbeelden worden opnieuw opgeslagen zonder EXIF, dus zonder GPS-locatie.
- **Paginamaat en aantal pagina's:** de PDF wordt nagemeten; het aantal pagina's is altijd even en komt minimaal op `min_paginas`.
