#!/usr/bin/env python3
"""Keuzebak van de fotoselectie-pipeline inlezen als curatie voor het album.

De pipeline (eqwise-dev/fotoselectie-pipeline) heeft het zware werk al gedaan: bursts,
scherpte, facet-score, soortherkenning met BioCLIP en de regionale checklist, sterren,
plaats uit het reisschema. Stap 5 schrijft dat IN de JPEG's (XMP en IPTC). Dit script
leest die velden terug en maakt er curatie.json van, zodat de workflow fotoalbum-bouw
direct kan beginnen; fotoalbum-selectie is dan niet nodig.

Gelezen velden:
  titel        XMP-dc:Title            Nederlandse soortnaam (of onderwerp)
  beschrijving XMP-dc:Description
  plek         XMP-iptcCore:Location   uit GPS of het reisschema
  land         XMP-photoshop:Country
  sterren      XMP-xmp:Rating          sterrenpiramide op facet-score
  label        XMP-xmp:Label           Green wildlife, Blue mensen, Yellow landschap/plant, Red onzeker
  taxonomie    XMP-lr:HierarchicalSubject  "Tanzania|Animalia|...|<soort>"

Gebruik:
  python3 fotoalbum/importeer_keuzebak.py <keuzebak-map> [--min-sterren 4] [--uit curatie.json]
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

from PIL import ExifTags, Image

LABEL_CATEGORIE = {"Green": "wildlife", "Blue": "mensen", "Yellow": "landschap", "Red": "onzeker"}
RANGEN = ["koninkrijk", "stam", "klasse", "orde", "familie", "geslacht", "soort"]


def xmp_pakket(pad):
    """Ruwe XMP-tekst uit een JPEG of TIFF (zonder exiftool)."""
    data = Path(pad).read_bytes()
    begin = data.find(b"<x:xmpmeta")
    eind = data.find(b"</x:xmpmeta>", begin)
    return data[begin:eind + 12].decode("utf-8", "replace") if begin >= 0 and eind > 0 else ""


def _waarde(xmp, tag):
    """Attribuut (tag="..."), element met tekst, of rdf:Alt/Bag/Seq met li's."""
    m = re.search(rf'{tag}="([^"]*)"', xmp)
    if m:
        return html.unescape(m.group(1))
    m = re.search(rf"<{tag}>(.*?)</{tag}>", xmp, re.S)
    if not m:
        return None
    lis = re.findall(r"<rdf:li[^>]*>(.*?)</rdf:li>", m.group(1), re.S)
    if lis:
        return [html.unescape(x.strip()) for x in lis]
    return html.unescape(m.group(1).strip())


def eerste(v):
    return v[0] if isinstance(v, list) else v


def lees(pad):
    xmp = xmp_pakket(pad)
    hier = _waarde(xmp, "lr:hierarchicalSubject") or []
    hier = hier if isinstance(hier, list) else [hier]
    langste = max((h.split("|") for h in hier), key=len, default=[])
    taxonomie = dict(zip(RANGEN, langste[1:]))  # eerste deel is de wortel ("Tanzania")
    label = eerste(_waarde(xmp, "xmp:Label")) or ""
    try:
        sterren = int(float(eerste(_waarde(xmp, "xmp:Rating")) or 0))
    except ValueError:
        sterren = 0
    tijd = None
    try:
        exif = Image.open(pad).getexif()
        tijd = exif.get_ifd(ExifTags.IFD.Exif).get(ExifTags.Base.DateTimeOriginal)
    except OSError:
        pass
    return {
        "titel": eerste(_waarde(xmp, "dc:title")) or "",
        "beschrijving": eerste(_waarde(xmp, "dc:description")) or "",
        "plek": eerste(_waarde(xmp, "Iptc4xmpCore:Location")) or "",
        "land": eerste(_waarde(xmp, "photoshop:Country")) or "",
        "sterren": sterren,
        "categorie": LABEL_CATEGORIE.get(label, "onzeker" if not label else label.lower()),
        "taxonomie": taxonomie,
        "tijd": str(tijd).strip() if tijd else "",
    }


def stam_zonder_nummer(naam):
    """'012 Lilaborstscharrelaar - DSC_1234.jpg' -> 'DSC_1234' (stabiele koppeling van de pipeline)."""
    return naam.rsplit(" - ", 1)[-1].rsplit(".", 1)[0] if " - " in naam else Path(naam).stem


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keuzebak")
    ap.add_argument("--min-sterren", type=int, default=4, help="albumwaardig vanaf dit aantal sterren")
    ap.add_argument("--uit", help="standaard: <keuzebak>/../uitvoer/selectie/curatie.json")
    args = ap.parse_args()
    basis = Path(args.keuzebak).expanduser().resolve()
    paden = sorted(p for p in basis.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".tif", ".tiff"))
    if not paden:
        sys.exit(f"Geen foto's gevonden in {basis}")
    momenten = []
    for n, pad in enumerate(paden, start=1):
        m = lees(pad)
        wet = m["taxonomie"].get("soort", "")
        onzeker = m["categorie"] == "onzeker"
        momenten.append({
            "id": n,
            "keuze": [str(pad.relative_to(basis))],
            "koppeling": stam_zonder_nummer(pad.name),
            "keuze_gewijzigd": False,
            "albumwaardig": m["sterren"] >= args.min_sterren and not onzeker,
            "kwaliteit": max(1, min(5, m["sterren"] or 1)),
            "categorie": m["categorie"],
            "soort": m["titel"] or "onbekend",
            "wetenschappelijke_naam": wet,
            "taxonomie": m["taxonomie"],
            # BioCLIP met regionale checklist; "onzeker" (rood label) laat de pipeline zelf al zien.
            "soort_status": "ONEENS: fotograaf beslist" if onzeker else ("zeker" if wet else "waarschijnlijk"),
            "soort_bron": "BioCLIP (fotoselectie-pipeline)",
            "beschrijving": m["beschrijving"],
            "plek": m["plek"],
            "land": m["land"],
            "tijd": m["tijd"],
            "opmerking": "BioCLIP was onzeker; controleer de soort" if onzeker else "",
        })
    uit = Path(args.uit) if args.uit else basis.parent / "uitvoer" / "selectie" / "curatie.json"
    uit.parent.mkdir(parents=True, exist_ok=True)
    uit.write_text(json.dumps({"fotomap": str(basis), "bron": "fotoselectie-pipeline", "momenten": momenten},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    waardig = [m for m in momenten if m["albumwaardig"]]
    plekken = sorted({m["plek"] for m in waardig if m["plek"]})
    print(f"{len(momenten)} foto's ingelezen, {len(waardig)} albumwaardig (≥ {args.min_sterren} sterren)")
    print(f"Plekken: {', '.join(plekken) or 'geen'}")
    print(f"Onzeker volgens BioCLIP: {sum(1 for m in momenten if m['categorie'] == 'onzeker')}")
    print(f"→ {uit}")


if __name__ == "__main__":
    main()
