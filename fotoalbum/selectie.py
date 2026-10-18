#!/usr/bin/env python3
"""Burst-selectie: groepeer bijna gelijke opnames en kies per moment de scherpste.

Gebruik:
  python3 fotoalbum/selectie.py pad/naar/fotos [--uit pad/naar/selectie] [--per-groep 1]

Leest fotos/origineel/ en fotos/bewerkt/ (of een platte map). Schrijft:
  selectie.json   groepen met per foto scherpte, belichting en de keuze
  groep-NNN.jpg   contactvel per groep: miniaturen met scherpte, plus de
                  scherpste uitsnede op ware grootte (om het oog te beoordelen)
  overzicht.html  alle groepen op één pagina, keuzes gemarkeerd

Een moment met een bewerkte versie (zelfde bestandsnaam of opnametijd binnen
de burst) krijgt automatisch de bewerkte versie als keuze.
"""

import argparse
import html
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import ExifTags, Image, ImageDraw, ImageFont, ImageOps

EXTENSIES = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".heic", ".webp"}
BURST_GAT_SEC = 1.5  # langere pauze = nieuw moment
BURST_MAX_VERSCHIL = 22  # dHash-afstand (van 64) waarboven het een ander beeld is
TEGELS = 8  # scherpte per tegel in een 8x8-raster; de vogel is het scherpe deel


def exif_tijd(img, pad):
    exif = img.getexif()
    sub = exif.get_ifd(ExifTags.IFD.Exif)
    tekst = sub.get(ExifTags.Base.DateTimeOriginal) or exif.get(ExifTags.Base.DateTime)
    if tekst:
        try:
            t = datetime.strptime(str(tekst).strip(), "%Y:%m:%d %H:%M:%S").timestamp()
            fractie = str(sub.get(ExifTags.Base.SubsecTimeOriginal, "") or "").strip()
            return t + (float("0." + fractie) if fractie.isdigit() else 0.0)
        except ValueError:
            pass
    return pad.stat().st_mtime


def exif_info(img):
    sub = img.getexif().get_ifd(ExifTags.IFD.Exif)
    info = {}
    for naam, sleutel in (("iso", ExifTags.Base.ISOSpeedRatings), ("brandpunt", ExifTags.Base.FocalLength),
                          ("sluitertijd", ExifTags.Base.ExposureTime)):
        if sleutel in sub:
            try:
                info[naam] = float(sub[sleutel])
            except (TypeError, ValueError):
                pass
    return info


def dhash(img):
    klein = np.asarray(img.convert("L").resize((9, 8), Image.BILINEAR), dtype=np.int16)
    return (klein[:, 1:] > klein[:, :-1]).flatten()


def scherpte(grijs):
    """Laplaciaan-variantie per tegel; score = gemiddelde van de 3 scherpste tegels.

    Een vogel tegen een onscherpe achtergrond beslaat een paar tegels; die
    bepalen of de foto 'scherp' is, niet de wazige rest.
    """
    a = grijs.astype(np.float32)
    lap = (-4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:])
    h, b = lap.shape
    th, tb = h // TEGELS, b // TEGELS
    waarden = []
    for i in range(TEGELS):
        for j in range(TEGELS):
            tegel = lap[i * th:(i + 1) * th, j * tb:(j + 1) * tb]
            waarden.append((float(tegel.var()), i, j))
    waarden.sort(reverse=True)
    beste = waarden[:3]
    return sum(w for w, _, _ in beste) / 3, (beste[0][1], beste[0][2])


def analyseer(pad, basis):
    img = ImageOps.exif_transpose(Image.open(pad))
    tijd, info = exif_tijd(img, pad), exif_info(img)
    rgb = img.convert("RGB")
    werk = rgb.copy()
    werk.thumbnail((1600, 1600))
    grijs = np.asarray(werk.convert("L"))
    score, tegel = scherpte(grijs)
    licht = np.asarray(werk.convert("L"), dtype=np.uint8)
    return {
        "bestand": str(pad.relative_to(basis)),
        "tijd": tijd,
        "breedte": rgb.width,
        "hoogte": rgb.height,
        "megapixel": round(rgb.width * rgb.height / 1e6, 1),
        "scherpte": round(score, 1),
        "scherpste_tegel": tegel,
        "uitgebeten_licht": round(float((licht >= 250).mean()), 3),
        "dichtgelopen_schaduw": round(float((licht <= 5).mean()), 3),
        "bewerkt": "bewerkt" in pad.relative_to(basis).parts,
        "_hash": dhash(rgb),
        **info,
    }


def groepeer(fotos):
    groepen, huidig = [], []
    for foto in sorted(fotos, key=lambda f: f["tijd"]):
        if huidig:
            vorige = huidig[-1]
            afstand = int((foto["_hash"] != vorige["_hash"]).sum())
            if foto["tijd"] - vorige["tijd"] > BURST_GAT_SEC or afstand > BURST_MAX_VERSCHIL:
                groepen.append(huidig)
                huidig = []
        huidig.append(foto)
    if huidig:
        groepen.append(huidig)
    # Een bewerkte versie die door bijsnijden of een andere tijd apart viel,
    # hoort bij de burst met het origineel van dezelfde naam.
    waar = {Path(f["bestand"]).stem: n for n, g in enumerate(groepen) for f in g if not f["bewerkt"]}
    for n, g in enumerate(groepen):
        for f in [f for f in g if f["bewerkt"]]:
            doel = waar.get(Path(f["bestand"]).stem)
            if doel is not None and doel != n:
                g.remove(f)
                groepen[doel].append(f)
    return [g for g in groepen if g]


def kies(groep, per_groep):
    bewerkt = [f for f in groep if f["bewerkt"]]
    if bewerkt:
        reden = "bewerkte versie aanwezig"
        # Melden als een onbewerkt frame uit dezelfde burst veel scherper is.
        scherpst = max(groep, key=lambda f: f["scherpte"])
        if not scherpst["bewerkt"] and scherpst["scherpte"] > 3 * max(f["scherpte"] for f in bewerkt):
            reden += f"; LET OP: {Path(scherpst['bestand']).name} is veel scherper"
        return [f["bestand"] for f in bewerkt], reden

    # Belichtingsfouten tellen mee: veel uitgebeten wit kost punten.
    def waarde(f):
        return f["scherpte"] * (1 - min(0.5, 4 * f["uitgebeten_licht"]))
    rang = sorted(groep, key=waarde, reverse=True)
    return [f["bestand"] for f in rang[:per_groep]], "scherpste opname"


def contactvel(groep, keuze, basis, pad):
    font = ImageFont.load_default(size=22)
    miniaturen = []
    for f in groep:
        img = ImageOps.exif_transpose(Image.open(basis / f["bestand"])).convert("RGB")
        mini = img.copy()
        mini.thumbnail((360, 360))
        miniaturen.append((f, img, mini))
    # Ware-grootte-uitsnede van de scherpste tegel van de beste foto.
    beste = next(m for m in miniaturen if m[0]["bestand"] == keuze[0])
    f, img, _ = beste
    i, j = f["scherpste_tegel"]
    cx, cy = (j + 0.5) / TEGELS * img.width, (i + 0.5) / TEGELS * img.height
    uitsnede = img.crop((int(cx - 300), int(cy - 300), int(cx + 300), int(cy + 300)))
    kolommen = min(4, len(miniaturen))
    rijen = -(-len(miniaturen) // kolommen)
    vel = Image.new("RGB", (kolommen * 380 + 20 + 620, max(rijen * 400 + 20, 640)), "#1f1f1f")
    teken = ImageDraw.Draw(vel)
    for n, (f, _, mini) in enumerate(miniaturen):
        x, y = 20 + (n % kolommen) * 380, 20 + (n // kolommen) * 400
        vel.paste(mini, (x, y))
        gekozen = f["bestand"] in keuze
        if gekozen:
            teken.rectangle([x - 4, y - 4, x + mini.width + 4, y + mini.height + 4], outline="#4ade80", width=6)
        teken.text((x, y + mini.height + 6), f"{n + 1}. scherpte {f['scherpte']:.0f}" + ("  KEUZE" if gekozen else ""),
                   fill="#4ade80" if gekozen else "#ddd", font=font)
    vel.paste(uitsnede, (kolommen * 380 + 20, 20))
    teken.text((kolommen * 380 + 20, 626), "100% uitsnede van de keuze", fill="#ddd", font=font)
    vel.save(pad, quality=85)


def overzicht(groepen, pad):
    kaarten = "\n".join(
        f'<section><h2>Groep {g["id"]} · {len(g["fotos"])} opname(s) · {html.escape(g["reden"])}</h2>'
        f'<img src="{g["contactvel"]}" loading="lazy" alt="Contactvel groep {g["id"]}"></section>'
        for g in groepen)
    pad.write_text(f"""<!doctype html><html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Fotoselectie</title>
<style>body{{margin:0;padding:16px;background:#151515;color:#eee;font:15px/1.5 Inter,system-ui,sans-serif}}
section{{margin:0 auto 32px;max-width:1600px}}h2{{font-size:15px;font-weight:600}}img{{max-width:100%;height:auto}}</style>
</head><body><h1>Fotoselectie: {len(groepen)} momenten</h1>
<p>Groen omrand = keuze. Wijzigingen: noem het groepnummer en het fotonummer.</p>{kaarten}</body></html>""",
                   encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fotomap")
    parser.add_argument("--uit", help="uitvoermap (standaard: <fotomap>/../uitvoer/selectie)")
    parser.add_argument("--per-groep", type=int, default=1, help="aantal keuzes per moment")
    args = parser.parse_args()
    basis = Path(args.fotomap).resolve()
    uit = Path(args.uit) if args.uit else basis.parent / "uitvoer" / "selectie"
    uit.mkdir(parents=True, exist_ok=True)
    paden = [p for p in sorted(basis.rglob("*")) if p.suffix.lower() in EXTENSIES
             and "verbeterd" not in p.relative_to(basis).parts]
    fotos = []
    for n, pad in enumerate(paden, start=1):
        try:
            fotos.append(analyseer(pad, basis))
        except OSError as fout:
            print(f"  ! overgeslagen {pad.name}: {fout}")
        if n % 50 == 0:
            print(f"  {n}/{len(paden)} geanalyseerd")
    groepen = []
    for n, groep in enumerate(groepeer(fotos), start=1):
        keuze, reden = kies(groep, args.per_groep)
        naam = f"groep-{n:03d}.jpg"
        contactvel(groep, keuze, basis, uit / naam)
        groepen.append({"id": n, "keuze": keuze, "reden": reden, "contactvel": naam,
                        "fotos": [{k: v for k, v in f.items() if not k.startswith("_")} for f in groep]})
    (uit / "selectie.json").write_text(json.dumps({"fotomap": str(basis), "groepen": groepen},
                                                  ensure_ascii=False, indent=2), encoding="utf-8")
    overzicht(groepen, uit / "overzicht.html")
    print(f"{len(fotos)} foto's, {len(groepen)} momenten, {sum(len(g['keuze']) for g in groepen)} gekozen → {uit}")


if __name__ == "__main__":
    main()
