"""Decoratieve locatorkaartjes als SVG (vector, dus haarscherp in de PDF).

Basiskaart: Natural Earth 1:50m landsgrenzen (publiek domein), vereenvoudigd
in kaartdata/landen.geojson. Een park of reservaat kan als eigen contour
meekomen (geometrie uit OpenStreetMap via plaatsen.py).
"""

import itertools
import json
import math
from functools import lru_cache
from pathlib import Path

LANDEN = Path(__file__).parent / "kaartdata" / "landen.geojson"
_TELLER = itertools.count(1)


@lru_cache(maxsize=1)
def landen():
    return json.loads(LANDEN.read_text(encoding="utf-8"))["features"]


def _ringen(geometrie):
    if geometrie["type"] == "Polygon":
        return [geometrie["coordinates"]]
    if geometrie["type"] == "MultiPolygon":
        return geometrie["coordinates"]
    return []


def _in_ring(lon, lat, ring):
    binnen = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi:
            binnen = not binnen
        j = i
    return binnen


def land_van(lon, lat):
    """(land-feature, index van het deelgebied) waarin het punt ligt, of (None, None)."""
    for land in landen():
        for n, polygoon in enumerate(_ringen(land["geometry"])):
            if _in_ring(lon, lat, polygoon[0]):
                return land, n
    return None, None


def _bbox(ringen):
    xs = [p[0] for r in ringen for p in r]
    ys = [p[1] for r in ringen for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def locator_svg(punten, park=None, breedte=360, hoogte=300, kleuren=None, label=None, nummers=None,
                inzet=True, vignet=True):
    """SVG-kaartje: het land of de landen van de punten, buurlanden vaag, park als accent, punten als stippen.

    punten: [(lon, lat), ...]; park: {"naam", "contour": [[[lon, lat], ...], ...]} of None;
    nummers: optioneel een label per punt (overzichtskaart met hoofdstuknummers).
    """
    k = {"land": "#e7e1d6", "buren": "#f1ede6", "rand": "#b9ae9c", "park": "#8a9a5b", "punt": "#b4532a",
         "tekst": "#5c564c", **(kleuren or {})}
    if not punten:
        return ""
    gevonden = [land_van(*p) for p in punten]
    eigen = []  # landen met een punt, met het deelgebied dat het punt bevat
    for land, deel in gevonden:
        if land is not None and all(land is not e[0] for e in eigen):
            eigen.append((land, deel))
    # Kader: per land het grootste deelgebied (context: heel Nederland, niet alleen Texel) en het
    # deelgebied met het punt, zonder verre overzeese delen. Op zee: alleen de punten.
    def grootste(land):
        ringen = [poly[0] for poly in _ringen(land["geometry"])]
        return max(ringen, key=lambda r: (lambda b: (b[2] - b[0]) * (b[3] - b[1]))(_bbox([r])))
    ingezoomd = bool(park and park.get("contour"))
    if ingezoomd:
        # Ingezoomd op het park; het land komt als klein inzetkaartje in de hoek.
        kader = _bbox(park["contour"] + [[list(p) for p in punten]])
        b = max(kader[2] - kader[0], kader[3] - kader[1]) * 0.6
        kader = (kader[0] - b, kader[1] - b, kader[2] + b, kader[3] + b)
    else:
        kader = _bbox([grootste(l) for l, _ in eigen] + [_ringen(l["geometry"])[d][0] for l, d in eigen]
                      + [[list(p) for p in punten]])
    x0, y0, x1, y1 = kader
    marge = 0 if ingezoomd else max(x1 - x0, y1 - y0) * 0.12 + 0.05
    x0, y0, x1, y1 = x0 - marge, y0 - marge, x1 + marge, y1 + marge
    breedtegraad = math.radians((y0 + y1) / 2)
    sx = math.cos(breedtegraad)
    schaal = min(breedte / ((x1 - x0) * sx), hoogte / (y1 - y0))
    ox = (breedte - (x1 - x0) * sx * schaal) / 2
    oy = (hoogte - (y1 - y0) * schaal) / 2

    def xy(lon, lat):
        return ox + (lon - x0) * sx * schaal, oy + (y1 - lat) * schaal

    def pad(ringen):
        delen = []
        for ring in ringen:
            pts = [xy(*p) for p in ring]
            delen.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
        return "".join(delen)

    def zichtbaar(ring):
        rx0, ry0, rx1, ry1 = _bbox([ring])
        return rx1 >= x0 and rx0 <= x1 and ry1 >= y0 and ry0 <= y1

    lagen = []
    eigen_landen = [l for l, _ in eigen]
    for ander in landen():
        if any(ander is l for l in eigen_landen):
            continue
        ringen = [poly[0] for poly in _ringen(ander["geometry"]) if zichtbaar(poly[0])]
        if ringen:
            lagen.append(f'<path d="{pad(ringen)}" fill="{k["buren"]}" stroke="{k["rand"]}" stroke-width=".4"/>')
    for land in eigen_landen:
        ringen = [poly[0] for poly in _ringen(land["geometry"]) if zichtbaar(poly[0])]
        lagen.append(f'<path d="{pad(ringen)}" fill="{k["land"]}" stroke="{k["rand"]}" stroke-width=".8"/>')
    if park and park.get("contour"):
        lagen.append(f'<path d="{pad(park["contour"])}" fill="{k["park"]}" fill-opacity=".35" '
                     f'stroke="{k["park"]}" stroke-width="1"/>')
    for n, (lon, lat) in enumerate(punten):
        x, y = xy(lon, lat)
        if nummers:
            lagen.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{k["punt"]}" stroke="#fff" stroke-width="1.5"/>'
                         f'<text x="{x:.1f}" y="{y + 3.6:.1f}" text-anchor="middle" font-size="10" font-weight="600" '
                         f'fill="#fff" class="kaartnummer">{nummers[n]}</text>')
        else:
            lagen.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{k["punt"]}" stroke="#fff" stroke-width="1.5"/>')
    if label:
        x, y = xy(*punten[0])
        anker = "end" if x > breedte * 0.6 else "start"
        dx = -10 if anker == "end" else 10
        lagen.append(f'<text x="{x + dx:.1f}" y="{y + 4:.1f}" text-anchor="{anker}" font-size="11" '
                     f'letter-spacing=".08em" fill="{k["tekst"]}" class="kaartlabel">{label}</text>')
    if ingezoomd and inzet:
        # Inzetkaartje rechtsboven: het hele land met een stip, zodat de lezer weet waar het park ligt.
        ib, ih = breedte * 0.3, hoogte * 0.3
        klein = locator_svg(punten[:1], breedte=ib, hoogte=ih, kleuren=kleuren, inzet=False, vignet=False)
        klein = klein.replace('<svg class="kaart"', f'<svg x="{breedte - ib - 4:.0f}" y="4" width="{ib:.0f}" height="{ih:.0f}"')
        lagen.append(f'<rect x="{breedte - ib - 6:.0f}" y="2" width="{ib + 4:.0f}" height="{ih + 4:.0f}" '
                     f'fill="{k["buren"]}" stroke="{k["rand"]}" stroke-width=".6"/>' + klein)
    if not vignet:
        return (f'<svg class="kaart" viewBox="0 0 {breedte:.0f} {hoogte:.0f}" xmlns="http://www.w3.org/2000/svg">'
                f'{"".join(lagen)}</svg>')
    # Zachte vignet: de kaart loopt naar de randen weg in het papier, geen harde uitsnede.
    n = next(_TELLER)
    return (f'<svg class="kaart" viewBox="0 0 {breedte} {hoogte}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="Kaart{": " + label if label else ""}"><defs>'
            f'<radialGradient id="kaartverloop{n}" cx="50%" cy="50%" r="62%">'
            f'<stop offset="72%" stop-color="#fff"/><stop offset="100%" stop-color="#000"/></radialGradient>'
            f'<mask id="kaartmasker{n}"><rect width="{breedte}" height="{hoogte}" fill="url(#kaartverloop{n})"/></mask>'
            f'</defs><g mask="url(#kaartmasker{n})">{"".join(lagen)}</g></svg>')


def coordinaten(lon, lat):
    """52°04′ N · 5°49′ O"""
    def dm(v, pos, neg):
        g = abs(v)
        return f"{int(g)}°{round((g - int(g)) * 60):02d}′ {pos if v >= 0 else neg}"
    return f"{dm(lat, 'N', 'Z')} · {dm(lon, 'O', 'W')}"
