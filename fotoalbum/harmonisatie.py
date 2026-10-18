"""Helderheid en kleur van alle albumfoto's licht in lijn brengen.

De stijl van het album komt van de bewerkte foto's (map "bewerkt/" of
"bewerkt": true in album.json); de andere foto's schuiven daar een stukje
naartoe. Bewerkte foto's zelf blijven ongemoeid.

Gemeten per foto, op een verkleinde kopie:
  helderheid  mediaan van de luminantie
  kleurzweem  gemiddelde R:G:B van bijna-neutrale pixels (grijs, wit,
              bewolkte lucht, stenen); verzadigde kleuren zoals een
              ijsvogel of blauwe lucht tellen niet mee, zodat de vogel
              zijn kleur houdt

De correctie is bewust voorzichtig: een fractie ("sterkte") van het
verschil, en altijd begrensd.
"""

import math

import numpy as np
from PIL import Image

MAX_GAMMA_STAP = 1.25  # gamma tussen 1/1.25 en 1.25: ongeveer een halve stop
MAX_KANAAL_STAP = 1.06  # hoogstens 6% per kleurkanaal
MIN_NEUTRAAL_AANDEEL = 0.03


def meet(img):
    klein = img.copy()
    klein.thumbnail((512, 512))
    rgb = np.asarray(klein, dtype=np.float32) / 255
    y = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    spreiding = rgb.max(axis=2) - rgb.min(axis=2)
    neutraal = (spreiding < 0.14) & (y > 0.15) & (y < 0.9)
    verhouding = None
    if neutraal.mean() >= MIN_NEUTRAAL_AANDEEL:
        gem = rgb[neutraal].mean(axis=0)
        verhouding = gem / gem.mean()
    return {"helderheid": float(np.clip(np.median(y), 0.03, 0.97)), "verhouding": verhouding}


def bepaal_doel(metingen, referenties):
    basis = [metingen[n] for n in referenties if n in metingen] or list(metingen.values())
    verhoudingen = [m["verhouding"] for m in basis if m["verhouding"] is not None]
    return {
        "helderheid": float(np.median([m["helderheid"] for m in basis])),
        "verhouding": np.median(verhoudingen, axis=0) if verhoudingen else np.ones(3, dtype=np.float32),
    }


def correctie(meting, doel, sterkte):
    gamma = math.log(doel["helderheid"]) / math.log(meting["helderheid"])
    gamma = min(MAX_GAMMA_STAP, max(1 / MAX_GAMMA_STAP, gamma ** sterkte))
    winst = np.ones(3)
    if meting["verhouding"] is not None:
        winst = np.clip((doel["verhouding"] / meting["verhouding"]) ** sterkte, 1 / MAX_KANAAL_STAP, MAX_KANAAL_STAP)
    # Verschuiving van de mediaan in stops: log2(m^gamma / m).
    stops = (gamma - 1) * math.log2(meting["helderheid"])
    return {"gamma": gamma, "winst": [float(w) for w in winst], "stops": stops}


def pas_toe(img, corr):
    if corr is None:
        return img
    banden = []
    for band, winst in zip(img.split(), corr["winst"]):
        tabel = [round(255 * min(1.0, (v / 255) * winst) ** corr["gamma"]) for v in range(256)]
        banden.append(band.point(tabel))
    return Image.merge("RGB", banden)


def omschrijf(corr):
    """Korte uitleg, bijvoorbeeld '+0.3 stop, warmer'."""
    stops = corr["stops"]
    delen = [f"{stops:+.1f} stop"] if abs(stops) >= 0.05 else []
    r, _, b = corr["winst"]
    if r - b > 0.015:
        delen.append("warmer")
    elif b - r > 0.015:
        delen.append("koeler")
    return ", ".join(delen) or "nauwelijks"


def contactvel(paren, pad):
    """Voor en na naast elkaar, één rij per gecorrigeerde foto."""
    if not paren:
        return
    rijh, marge = 220, 12
    rijen = []
    for voor, na in paren:
        rij = []
        for img in (voor, na):
            kopie = img.copy()
            kopie.thumbnail((10_000, rijh))
            rij.append(kopie)
        rijen.append(rij)
    breedte = max(sum(i.width for i in rij) for rij in rijen) + 3 * marge
    vel = Image.new("RGB", (breedte, len(rijen) * (rijh + marge) + marge), "#2b2b2b")
    y = marge
    for voor, na in rijen:
        vel.paste(voor, (marge, y))
        vel.paste(na, (2 * marge + voor.width, y))
        y += rijh + marge
    vel.save(pad, quality=88)
