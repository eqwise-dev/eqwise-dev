"""GPS uit foto's en plaatsnamen: plaats, regio, land en natuurgebied.

Bronnen (OpenStreetMap, gratis, met beleefde limieten):
  Nominatim  omgekeerd geocoderen: plaats, provincie, land
  Overpass   in welk park of reservaat ligt het punt (nationaal park,
             beschermd gebied, natuurreservaat), plus de contour voor de kaart

Alles wordt bewaard in plaatsen-cache.json naast album.json, zodat elk punt
maar één keer wordt opgevraagd en het album daarna offline bouwt. Zonder
internet of bij een fout: geen naam, en album.json kan "plek" handmatig zetten.
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import ExifTags, Image

AGENT = "eqwise-fotoalbum/1.0 (+https://eqwise.nl)"  # Nominatim eist een herkenbare User-Agent
NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
OVERPASS = "https://overpass-api.de/api/interpreter"


def gps(pad):
    """(lon, lat) uit EXIF, of None."""
    try:
        info = Image.open(pad).getexif().get_ifd(ExifTags.IFD.GPSInfo)
    except OSError:
        return None
    if not info or 2 not in info or 4 not in info:
        return None

    def graden(waarde, ref):
        g, m, s = (float(x) for x in waarde)
        v = g + m / 60 + s / 3600
        return -v if ref in ("S", "W") else v

    try:
        return graden(info[4], info.get(3, "E")), graden(info[2], info.get(1, "N"))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september",
           "oktober", "november", "december"]


def opnametijd(pad):
    """datetime van de opname uit EXIF, of None."""
    from datetime import datetime
    try:
        exif = Image.open(pad).getexif()
    except OSError:
        return None
    tekst = exif.get_ifd(ExifTags.IFD.Exif).get(ExifTags.Base.DateTimeOriginal) or exif.get(ExifTags.Base.DateTime)
    try:
        return datetime.strptime(str(tekst).strip(), "%Y:%m:%d %H:%M:%S") if tekst else None
    except ValueError:
        return None


def periode(tijden):
    """'mei 2026', 'april – juni 2025' of 'december 2024 – januari 2025'."""
    tijden = sorted(t for t in tijden if t)
    if not tijden:
        return ""
    a, b = tijden[0], tijden[-1]
    if (a.year, a.month) == (b.year, b.month):
        return f"{MAANDEN[a.month - 1]} {a.year}"
    if a.year == b.year:
        return f"{MAANDEN[a.month - 1]} – {MAANDEN[b.month - 1]} {a.year}"
    return f"{MAANDEN[a.month - 1]} {a.year} – {MAANDEN[b.month - 1]} {b.year}"


class Plaatsen:
    def __init__(self, cache_pad, online=True):
        self.pad = Path(cache_pad)
        self.cache = json.loads(self.pad.read_text(encoding="utf-8")) if self.pad.exists() else {}
        self.online = online
        self._laatst = 0.0

    def bewaar(self):
        self.pad.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1), encoding="utf-8")

    def zoek(self, lon, lat):
        """{"plaats", "regio", "land", "gebied", "gebied_id"} voor een punt (op ~100 m afgerond)."""
        sleutel = f"{lat:.3f},{lon:.3f}"
        if sleutel not in self.cache and self.online:
            try:
                self.cache[sleutel] = {**self._adres(lon, lat), **self._gebied(lon, lat)}
                self.bewaar()
            except OSError as fout:
                print(f"  ! plaats onbekend voor {sleutel}: {fout}")
                return {}
        return self.cache.get(sleutel, {})

    def contour(self, gebied_id):
        """Buitenrand van een park als [[ [lon, lat], ... ], ...], ook gecachet."""
        sleutel = f"contour:{gebied_id}"
        if sleutel not in self.cache and self.online and gebied_id:
            soort, nummer = gebied_id.split("/")
            try:
                data = self._overpass(f"[out:json][timeout:60];{soort}({nummer});out geom;")
                ringen = []
                for el in data.get("elements", []):
                    if el.get("type") == "way" and "geometry" in el:
                        ringen.append([[round(p["lon"], 4), round(p["lat"], 4)] for p in el["geometry"]])
                    for lid in el.get("members", []):
                        if lid.get("role") in ("outer", "") and "geometry" in lid:
                            ringen.append([[round(p["lon"], 4), round(p["lat"], 4)] for p in lid["geometry"]])
                self.cache[sleutel] = ringen
                self.bewaar()
            except OSError as fout:
                print(f"  ! contour onbekend voor {gebied_id}: {fout}")
                return []
        return self.cache.get(sleutel, [])

    # ---------- bronnen ----------

    def _haal(self, url, data=None):
        # Nominatim en Overpass vragen hoogstens ongeveer één verzoek per seconde.
        wacht = 1.1 - (time.monotonic() - self._laatst)
        if wacht > 0:
            time.sleep(wacht)
        verzoek = urllib.request.Request(url, data=data, headers={"User-Agent": AGENT, "Accept-Language": "nl,en"})
        with urllib.request.urlopen(verzoek, timeout=60) as antwoord:
            self._laatst = time.monotonic()
            return json.loads(antwoord.read().decode("utf-8"))

    def _overpass(self, query):
        return self._haal(OVERPASS, urllib.parse.urlencode({"data": query}).encode())

    def _adres(self, lon, lat):
        url = NOMINATIM + "?" + urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 12})
        a = self._haal(url).get("address", {})
        return {
            "plaats": a.get("village") or a.get("town") or a.get("city") or a.get("municipality") or a.get("county"),
            "regio": a.get("state") or a.get("province") or a.get("region"),
            "land": a.get("country"),
        }

    def _gebied(self, lon, lat):
        q = (f"[out:json][timeout:30];is_in({lat},{lon})->.a;"
             "(area.a[boundary=national_park];area.a[boundary=protected_area];area.a[leisure=nature_reserve];);"
             "out tags;")
        kandidaten = []
        for el in self._overpass(q).get("elements", []):
            t = el.get("tags", {})
            naam = t.get("name:nl") or t.get("name")
            if not naam:
                continue
            # Area-id terug naar het OSM-object: 3600000000+ is een relatie, 2400000000+ een way.
            aid = el["id"]
            obj = f"relation/{aid - 3600000000}" if aid >= 3600000000 else f"way/{aid - 2400000000}"
            rang = 0 if t.get("boundary") == "national_park" else 1 if t.get("leisure") == "nature_reserve" else 2
            kandidaten.append((rang, naam, obj))
        if not kandidaten:
            return {"gebied": None, "gebied_id": None}
        _, naam, obj = sorted(kandidaten)[0]
        return {"gebied": naam, "gebied_id": obj}
