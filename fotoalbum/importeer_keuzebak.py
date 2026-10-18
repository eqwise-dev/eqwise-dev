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
    tijd, camera = None, ""
    try:
        exif = Image.open(pad).getexif()
        tijd = exif.get_ifd(ExifTags.IFD.Exif).get(ExifTags.Base.DateTimeOriginal)
        merk, model = str(exif.get(ExifTags.Base.Make) or "").strip(), str(exif.get(ExifTags.Base.Model) or "").strip()
        camera = model if model.lower().startswith(merk.lower()[:4]) or not merk else f"{merk} {model}"
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
        "maker": eerste(_waarde(xmp, "dc:creator")) or "",
        "camera": camera.strip(),
    }


def stam_zonder_nummer(naam):
    """'012 Lilaborstscharrelaar - DSC_1234.jpg' -> 'DSC_1234' (stabiele koppeling van de pipeline)."""
    return naam.rsplit(" - ", 1)[-1].rsplit(".", 1)[0] if " - " in naam else Path(naam).stem


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keuzebak")
    ap.add_argument("--min-sterren", type=int, default=4, help="albumwaardig vanaf dit aantal sterren")
    ap.add_argument("--uit", help="standaard: <keuzebak>/../uitvoer/selectie/curatie.json")
    ap.add_argument("--maker", help="maker voor foto's zonder dc:creator (bijv. de reisvriend van deze map)")
    ap.add_argument("--tijdverschil", action="append", default=[], metavar="WIE=MINUTEN",
                    help="klok gelijkzetten per toestel: 'Anne|NIKON Z 6=-60', of per maker 'Anne=-60' "
                         "of per cameramodel 'ILCE-7RM5=+5' (herhaalbaar; toestel wint van maker)")
    ap.add_argument("--apparaten", action="store_true",
                    help="alleen tonen welke toestellen per maker voorkomen, met eerste en laatste opnametijd")
    ap.add_argument("--voeg-toe", action="store_true", help="aan een bestaande curatie.json toevoegen (meerdere fotografen)")
    args = ap.parse_args()
    verschil = {k.strip(): int(v) for k, v in (t.rsplit("=", 1) for t in args.tijdverschil)}
    basis = Path(args.keuzebak).expanduser().resolve()
    paden = sorted(p for p in basis.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".tif", ".tiff"))
    if not paden:
        sys.exit(f"Geen foto's gevonden in {basis}")
    uit = Path(args.uit) if args.uit else basis.parent / "uitvoer" / "selectie" / "curatie.json"
    bestaand = json.loads(uit.read_text(encoding="utf-8")) if args.voeg_toe and uit.exists() else None
    momenten = bestaand["momenten"] if bestaand else []
    begin_id = max((m["id"] for m in momenten), default=0)
    for n, pad in enumerate(paden, start=begin_id + 1):
        m = lees(pad)
        maker = m["maker"] or args.maker or ""
        tijd = m["tijd"]
        # Telefoons zetten hun klok zelf gelijk via het netwerk; camera's niet. Daarom per toestel.
        minuten = verschil.get(f"{maker}|{m['camera']}", verschil.get(m["camera"], verschil.get(maker)))
        if tijd and minuten:
            from datetime import datetime, timedelta
            tijd = (datetime.strptime(tijd, "%Y:%m:%d %H:%M:%S") + timedelta(minutes=minuten)).strftime("%Y:%m:%d %H:%M:%S")
        wet = m["taxonomie"].get("soort", "")
        onzeker = m["categorie"] == "onzeker"
        momenten.append({
            "id": n,
            # Absoluut pad: bij meerdere fotografen staan de foto's in verschillende mappen.
            "keuze": [str(pad)],
            "maker": maker,
            "camera": m["camera"],
            "telefoon": bool(re.search(r"iphone|pixel|galaxy|^sm-|oneplus|xiaomi|huawei|oppo", m["camera"], re.I)),
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
            "tijd": tijd,
            "opmerking": "BioCLIP was onzeker; controleer de soort" if onzeker else "",
        })
    if args.apparaten:
        per = {}
        for m in momenten:
            per.setdefault((m.get("maker") or "?", m.get("camera") or "?"), []).append(m.get("tijd") or "")
        for (maker, camera), tijden in sorted(per.items()):
            t = sorted(x for x in tijden if x)
            soort = "telefoon" if re.search(r"iphone|pixel|galaxy|^sm-", camera, re.I) else "camera"
            print(f"{maker:18s} {camera:28s} {soort:9s} {len(tijden):5d} foto's  {t[0] if t else '-'}  →  {t[-1] if t else '-'}")
        print("\nZet het klokverschil per camera: --tijdverschil 'Naam|Model=MINUTEN'. Telefoons staan meestal goed.")
        return
    uit.parent.mkdir(parents=True, exist_ok=True)
    fotomappen = sorted(set((bestaand or {}).get("fotomappen", [])) | {str(basis)})
    makers = sorted({m.get("maker") for m in momenten if m.get("maker")})
    uit.write_text(json.dumps({"fotomap": fotomappen[0], "fotomappen": fotomappen, "makers": makers,
                               "bron": "fotoselectie-pipeline", "momenten": momenten},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    waardig = [m for m in momenten if m["albumwaardig"]]
    plekken = sorted({m["plek"] for m in waardig if m["plek"]})
    print(f"{len(momenten)} foto's ingelezen, {len(waardig)} albumwaardig (≥ {args.min_sterren} sterren)")
    print(f"Plekken: {', '.join(plekken) or 'geen'}")
    print(f"Onzeker volgens BioCLIP: {sum(1 for m in momenten if m['categorie'] == 'onzeker')}")
    print(f"Fotografen: {', '.join(makers) or 'onbekend'}")
    print(f"→ {uit}")


if __name__ == "__main__":
    main()
