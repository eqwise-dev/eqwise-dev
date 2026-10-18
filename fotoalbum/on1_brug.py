#!/usr/bin/env python3
"""Brug naar ON1 Photo RAW via Folder Actions (ON1 heeft geen API of opdrachtregel).

Eenmalig in ON1 instellen (zie README): een Folder Action op de map "in" die
de album-preset toepast (NoNoise AI, eventueel Resize AI) en exporteert naar
de map "uit", op volle grootte, JPG 95+ of TIFF, sRGB, zonder exportverscherping.

Gebruik:
  python3 fotoalbum/on1_brug.py stuur album.json   # werklijst naar ON1-map "in"
  python3 fotoalbum/on1_brug.py haal  album.json   # wachten op ON1 en resultaten ophalen

"stuur" leest uitvoer/te-verbeteren.json (geschreven door build.py). "haal"
zet de resultaten in fotos/verbeterd/, waar build.py ze automatisch voorrang geeft.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

EXTENSIES = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}


def lees(album_pad):
    album_pad = Path(album_pad).resolve()
    data = json.loads(album_pad.read_text(encoding="utf-8"))
    on1 = data.get("on1")
    if not on1:
        sys.exit('Geen "on1": {"in": ..., "uit": ...} in album.json.')
    basis = album_pad.parent
    fotomap = basis / data.get("fotomap", "fotos")
    uitvoer = basis / data.get("uitvoermap", "uitvoer")
    return fotomap, uitvoer, Path(on1["in"]).expanduser(), Path(on1["uit"]).expanduser(), on1


def stuur(album_pad):
    fotomap, uitvoer, map_in, _, _ = lees(album_pad)
    lijst_pad = uitvoer / "te-verbeteren.json"
    if not lijst_pad.exists():
        sys.exit("Eerst build.py draaien; dat schrijft uitvoer/te-verbeteren.json.")
    lijst = json.loads(lijst_pad.read_text(encoding="utf-8"))
    map_in.mkdir(parents=True, exist_ok=True)
    verstuurd = []
    for item in lijst:
        bron = fotomap / item["bestand"]
        if any((fotomap / "verbeterd").glob(bron.stem + ".*")):
            print(f"  {item['bestand']}: al verbeterd door ON1 ({item['dpi']} dpi), niet opnieuw verstuurd.")
            continue
        if item["factor"] > 2.2:
            print(f"  ! {item['bestand']}: {item['dpi']} dpi vraagt {item['factor']}x; meer dan 2x ziet er zelden "
                  "goed uit. Liever kleiner plaatsen; toch verstuurd.")
        shutil.copy2(bron, map_in / bron.name)
        verstuurd.append(bron.stem)
    (uitvoer / "on1-verstuurd.json").write_text(json.dumps(verstuurd, indent=2), encoding="utf-8")
    print(f"{len(verstuurd)} foto's in {map_in}. ON1 verwerkt ze via de Folder Action.")


def haal(album_pad, wacht_min):
    fotomap, uitvoer, _, map_uit, _ = lees(album_pad)
    verwacht = set(json.loads((uitvoer / "on1-verstuurd.json").read_text(encoding="utf-8")))
    doel = fotomap / "verbeterd"
    doel.mkdir(parents=True, exist_ok=True)
    einde = time.monotonic() + wacht_min * 60
    groottes = {}
    while True:
        klaar = {}
        for pad in map_uit.glob("*"):
            # ON1 kan een achtervoegsel toevoegen (IMG_1234-Edit.jpg); koppel op het begin.
            stam = next((s for s in verwacht if pad.stem == s or pad.stem.startswith(s + "-")), None)
            if not stam or pad.suffix.lower() not in EXTENSIES:
                continue
            # Klaar als de grootte sinds de vorige ronde gelijk bleef: ON1 schrijft niet meer.
            grootte = pad.stat().st_size
            if grootte > 0 and groottes.get(pad) == grootte:
                klaar[stam] = pad
            groottes[pad] = grootte
        if len(klaar) == len(verwacht) or time.monotonic() > einde:
            break
        print(f"  {len(klaar)}/{len(verwacht)} klaar, wachten op ON1...")
        time.sleep(3 if not klaar and not groottes else 10)
    for stam, pad in klaar.items():
        shutil.copy2(pad, doel / (stam + pad.suffix.lower()))
    ontbreekt = sorted(verwacht - set(klaar))
    print(f"{len(klaar)} verbeterde foto's in {doel}.")
    if ontbreekt:
        print(f"  ! nog niet terug van ON1: {', '.join(ontbreekt)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("actie", choices=["stuur", "haal"])
    parser.add_argument("album")
    parser.add_argument("--wacht", type=float, default=30, help="minuten wachten op ON1 (haal)")
    args = parser.parse_args()
    if args.actie == "stuur":
        stuur(args.album)
    else:
        haal(args.album, args.wacht)


if __name__ == "__main__":
    main()
