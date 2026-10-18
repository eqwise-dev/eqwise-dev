#!/usr/bin/env python3
"""EQwise fotoalbum: één bron (album.json), twee uitvoeren.

  print/  drukklare PDF met losse pagina's voor Blurb "PDF to Book"
  web/    snelle, vindbare verhaalpagina met WebP-srcset en schema.org

Gebruik:
  python3 fotoalbum/build.py pad/naar/album.json [--alleen print|web] [--proef]

Foto's staan in de map "fotos" naast album.json (instelbaar met "fotomap").
"""

import argparse
from datetime import timedelta
import html
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageCms, ImageEnhance, ImageOps

import harmonisatie
import iconen
import kaft
import kaart
import plaatsen

FONTS = Path(__file__).parent / "fonts"
# OpenStreetMap-gegevens (ODbL) vragen naamsvermelding; Natural Earth is publiek domein.
KAARTBRON = "Kaartgegevens: Natural Earth, © OpenStreetMap-bijdragers"
GOOGLE_DISCLAIMER = (". Luchtbeelden: Google Earth. Google Earth is een handelsmerk van Google LLC; "
                     "dit boek is niet verbonden aan of goedgekeurd door Google.")

CHROME_KANDIDATEN = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "chromium",
    "chromium-browser",
    "google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

# Layouts: per pagina een lijst vakken (x, y, b, h) als fractie van het
# bijgesneden paginavlak. Vakken die de rand raken lopen door in de afloop.
LAYOUTS = {
    "vol": [(0, 0, 1, 1)],
    "duo": [(0, 0, 0.5, 1), (0.5, 0, 0.5, 1)],
    "drie": [(0, 0, 0.62, 1), (0.62, 0, 0.38, 0.5), (0.62, 0.5, 0.38, 0.5)],
    "vier": [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)],
    "passe-partout": [(0.12, 0.12, 0.76, 0.66)],
}
LAYOUT_TUSSENRUIMTE_IN = 0.08

STANDAARD_STIJL = {
    "achtergrond": "#faf8f5",
    "tekst": "#1d1c1a",
    "accent": "#b4532a",
    "koppen": "'Cormorant Garamond', Caladea, Georgia, serif",
    "schreefloos": "Inter, 'Liberation Sans', sans-serif",
}


def kopieer_fonts(doel, web=False):
    """Lettertypen naast de HTML zetten; voor het web als lichte WOFF2 met alleen Latijnse tekens."""
    doel.mkdir(parents=True, exist_ok=True)
    for bron in FONTS.glob("*.ttf"):
        if not web:
            shutil.copy2(bron, doel / bron.name)
            continue
        uit = doel / (bron.stem + ".woff2")
        if uit.exists():
            continue
        try:
            from fontTools import subset
            opties = subset.Options()
            opties.flavor = "woff2"
            opties.layout_features = ["*"]
            font = subset.load_font(str(bron), opties)
            sub = subset.Subsetter(opties)
            sub.populate(unicodes=list(range(0x20, 0x250)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D,
                                                               0x2026, 0x2032, 0x2033, 0x00B7, 0x00B0])
            sub.subset(font)
            subset.save_font(font, str(uit), opties)
        except ImportError:
            shutil.copy2(bron, doel / bron.name)


def vind_chrome():
    for kandidaat in CHROME_KANDIDATEN:
        pad = shutil.which(kandidaat) or (kandidaat if Path(kandidaat).exists() else None)
        if pad:
            return pad
    sys.exit("Geen Chrome of Chromium gevonden voor het maken van de PDF.")


def open_foto(pad):
    """Opent een foto rechtop gedraaid en in sRGB."""
    img = ImageOps.exif_transpose(Image.open(pad))
    icc = img.info.get("icc_profile")
    if icc:
        try:
            bron = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            img = ImageCms.profileToProfile(img, bron, ImageCms.createProfile("sRGB"), outputMode="RGB")
        except (ImageCms.PyCMSError, OSError):
            pass
    return img.convert("RGB")


class Album:
    def __init__(self, album_pad):
        self.pad = Path(album_pad).resolve()
        self.data = json.loads(self.pad.read_text(encoding="utf-8"))
        self.fotomap = self.pad.parent / self.data.get("fotomap", "fotos")
        self.uit = self.pad.parent / self.data.get("uitvoermap", "uitvoer")
        d = self.data["drukker"]
        self.afloop = d["afloop_in"]
        self.pag_b = d["pagina_breedte_in"]  # inclusief afloop
        self.pag_h = d["pagina_hoogte_in"]
        self.trim_b = self.pag_b - 2 * self.afloop
        self.trim_h = self.pag_h - 2 * self.afloop
        self.veilig = d["veilige_marge_in"]
        self.dpi_min = d.get("dpi_min", 200)
        self.dpi_doel = d.get("dpi_doel", 300)
        self.waarschuwingen = []
        self.te_verbeteren = {}  # bestand -> laagste dpi over alle plaatsingen
        self.correcties = self._bereken_harmonisatie()
        self.locaties = self._bereken_locaties()
        self.paginas = self._bouw_paginas()

    # ---------- foto's laden en in lijn brengen ----------

    def alle_fotos(self):
        gezien = {}
        for hoofdstuk in self.data["hoofdstukken"]:
            for pagina in hoofdstuk["paginas"]:
                for foto in pagina["fotos"]:
                    gezien.setdefault(foto["bestand"], foto)
        return gezien

    @staticmethod
    def is_bewerkt(foto):
        return foto.get("bewerkt", Path(foto["bestand"]).parts[0] == "bewerkt")

    def _bereken_harmonisatie(self):
        instelling = {"aan": True, "sterkte": 0.6, **self.data.get("harmoniseren", {})}
        if not instelling["aan"]:
            return {}
        fotos = self.alle_fotos()
        metingen = {naam: harmonisatie.meet(open_foto(self.bronpad(naam))) for naam in fotos}
        referenties = [naam for naam, foto in fotos.items() if self.is_bewerkt(foto)]
        doel = harmonisatie.bepaal_doel(metingen, referenties)
        correcties = {}
        for naam, foto in fotos.items():
            if self.is_bewerkt(foto) or foto.get("harmoniseren") is False:
                continue
            corr = harmonisatie.correctie(metingen[naam], doel, instelling["sterkte"])
            correcties[naam] = corr
            if harmonisatie.omschrijf(corr) != "nauwelijks":
                self.waarschuwingen.append(f"KLEUR    {naam}: {harmonisatie.omschrijf(corr)}")
        return correcties

    def _bereken_locaties(self):
        """Per hoofdstuk: GPS-punten, plaats/regio/land/natuurgebied, parkcontour en periode."""
        instelling = {"online": True, **self.data.get("plaatsen", {})}
        register = plaatsen.Plaatsen(self.pad.parent / "plaatsen-cache.json", online=instelling["online"])
        uit = []
        # Camera's zonder GPS: plekken lenen van telefoonfoto's uit dezelfde tijd (map fotos/telefoon/).
        # Staat de cameraklok niet op lokale tijd (bijv. nog op Nederlandse tijd in Tanzania), zet dan
        # "camera_tijdverschil_min" (minuten die bij de cameratijd opgeteld moeten worden).
        telefoon = [(t, g) for t, g in ((plaatsen.opnametijd(p), plaatsen.gps(p))
                                        for p in sorted((self.fotomap / "telefoon").glob("*"))
                                        if p.suffix.lower() in (".jpg", ".jpeg", ".heic", ".png")) if t and g]
        verschil = timedelta(minutes=instelling.get("camera_tijdverschil_min", 0))
        for hoofdstuk in self.data["hoofdstukken"]:
            bestanden = [self.fotomap / f["bestand"] for p in hoofdstuk["paginas"] for f in p["fotos"]]
            punten = [g for g in (plaatsen.gps(b) for b in bestanden) if g]
            if not punten and telefoon:
                tijden = [t for t in self._tijden(hoofdstuk, verschil) if t]
                if tijden:
                    van, tot = min(tijden) - timedelta(hours=1), max(tijden) + timedelta(hours=1)
                    punten = [g for t, g in telefoon if van <= t <= tot]
            if hoofdstuk.get("gps"):  # handmatig: [lat, lon]
                punten = [(hoofdstuk["gps"][1], hoofdstuk["gps"][0])]
            info = register.zoek(*punten[0]) if punten else {}
            contour = register.contour(info.get("gebied_id")) if info.get("gebied_id") else []
            # Land: OpenStreetMap, anders handmatig, anders de kaart zelf (werkt ook offline).
            land = info.get("land") or hoofdstuk.get("land") or self.data.get("land")
            if not land and punten:
                gevonden, _ = kaart.land_van(*punten[0])
                land = gevonden["properties"]["naam"] if gevonden else None
            onderdelen = [hoofdstuk.get("plek") or info.get("gebied") or info.get("plaats"),
                          info.get("regio") if not hoofdstuk.get("plek") else None, land]
            regel = " · ".join(dict.fromkeys(o for o in onderdelen if o))
            uit.append({
                "punten": punten,
                "midden": (sum(p[0] for p in punten) / len(punten), sum(p[1] for p in punten) / len(punten)) if punten else None,
                "plekregel": regel,
                "korte_naam": hoofdstuk.get("plek") or info.get("gebied") or info.get("plaats") or "",
                "park": {"naam": info.get("gebied"), "contour": contour} if contour else None,
                "periode": hoofdstuk.get("periode") or plaatsen.periode(self._tijden(hoofdstuk, timedelta(0))),
                "icoon": hoofdstuk.get("icoon") or iconen.kies(hoofdstuk["titel"], hoofdstuk.get("intro"), regel,
                                                               hoofdstuk.get("thema")),
            })
        return uit

    def credits_plek(self):
        """'eind' (standaard, alleen in het colofon), 'begin' (titelpagina), 'begin_en_eind' of 'per_foto'."""
        return self.data.get("fotocredits", "eind")

    def credit(self, pagina):
        """'Foto: Anne' voor foto's van een ander dan de maker van het album (de eigen foto's krijgen niets)."""
        if self.credits_plek() != "per_foto":
            return ""
        eigen = self.data.get("maker", "").split(" · ")[0].strip()
        anderen = list(dict.fromkeys(f["maker"] for f in pagina.get("fotos", [])
                                     if f.get("maker") and f["maker"] != eigen))
        return f"Foto: {html.escape(' & '.join(anderen))}" if anderen else ""

    def medefotografen(self):
        eigen = self.data.get("maker", "").split(" · ")[0].strip()
        return list(dict.fromkeys(f["maker"] for h in self.data["hoofdstukken"] for p in h["paginas"]
                                  for f in p["fotos"] if f.get("maker") and f["maker"] != eigen))

    def colofon_regels(self):
        maker = self.data.get("maker", "").split(" · ")[0].strip()
        regels = []
        if maker:
            regels.append(("Foto's en tekst", maker))
        if self.medefotografen() and self.credits_plek() in ("eind", "begin_en_eind", "per_foto"):
            regels.append(("Met foto's van", ", ".join(self.medefotografen())))
        if any(l["punten"] for l in self.locaties):
            regels.append(("Kaarten", "Natural Earth; © OpenStreetMap-bijdragers"))
        if self.heeft_luchtfoto():
            regels.append(("Luchtbeelden", GOOGLE_DISCLAIMER.lstrip(". ").replace("Luchtbeelden: ", "")))
        regels.append(("Lettertype", "Cormorant Garamond (SIL Open Font License)"))
        jaar = self.data.get("jaar") or next((l["periode"].split()[-1] for l in self.locaties if l["periode"]), "")
        if maker:
            regels.append(("", f"© {jaar} {maker}".replace("  ", " ")))
        return regels

    def colofon_html(self):
        rijen = "".join(f'<p><span>{html.escape(k)}</span>{html.escape(v)}</p>' if k else f'<p class="recht">{html.escape(v)}</p>'
                        for k, v in self.colofon_regels())
        return f'<p class="kicker">Colofon</p><h3>{html.escape(self.data["titel"])}</h3>{rijen}'

    def heeft_luchtfoto(self):
        return any(h.get("luchtfoto") for h in self.data["hoofdstukken"])

    def _tijden(self, hoofdstuk, verschil):
        """Opnametijden van een hoofdstuk. Een "tijd" per foto (al gelijkgezet per toestel door
        importeer_keuzebak.py) gaat voor; anders EXIF plus het algemene cameraverschil."""
        from datetime import datetime
        uit = []
        for p in hoofdstuk["paginas"]:
            for f in p["fotos"]:
                if f.get("tijd"):
                    try:
                        uit.append(datetime.strptime(f["tijd"], "%Y:%m:%d %H:%M:%S"))
                        continue
                    except ValueError:
                        pass
                t = plaatsen.opnametijd(self.fotomap / f["bestand"])
                uit.append(t + verschil if t else None)
        return uit

    def kaart_svg(self, h_idx, breedte=360, hoogte=300, label=False):
        """Klein kaartje zonder label (de plek staat al in de tekst); groot kaartje met label."""
        loc = self.locaties[h_idx]
        if not loc["punten"]:
            return ""
        return kaart.locator_svg(loc["punten"], park=loc["park"], breedte=breedte, hoogte=hoogte,
                                 label=html.escape(loc["korte_naam"]) if label and loc["korte_naam"] else None)

    def overzicht_svg(self, breedte=720, hoogte=520):
        punten = [(l["midden"], n + 1) for n, l in enumerate(self.locaties) if l["midden"]]
        if not punten:
            return ""
        return kaart.locator_svg([p for p, _ in punten], breedte=breedte, hoogte=hoogte,
                                 nummers=[f"{n}" for _, n in punten])

    def bronpad(self, naam):
        """Verbeterde versie uit ON1 (fotos/verbeterd/<naam>.*) gaat voor op het origineel."""
        verbeterd = sorted((self.fotomap / "verbeterd").glob(Path(naam).stem + ".*"))
        return verbeterd[0] if verbeterd else self.fotomap / naam

    def laad(self, foto):
        return harmonisatie.pas_toe(open_foto(self.bronpad(foto["bestand"])), self.correcties.get(foto["bestand"]))

    def maak_contactvel(self, pad):
        paren = []
        for naam, corr in self.correcties.items():
            if harmonisatie.omschrijf(corr) == "nauwelijks":
                continue
            voor = open_foto(self.bronpad(naam))
            voor.thumbnail((800, 800))
            paren.append((voor, harmonisatie.pas_toe(voor, corr)))
        harmonisatie.contactvel(paren, pad)

    # ---------- inhoud naar pagina's ----------

    def _bouw_paginas(self):
        # Pagina 1 (rechts): albumtitel. Pagina 2 (links): overzichtskaart of leeg.
        paginas = [{"type": "albumtitel"}, {"type": "overzicht"}]
        for h_idx, hoofdstuk in enumerate(self.data["hoofdstukken"]):
            # Een opening staat bij voorkeur rechts. Valt hij links, dan wordt de
            # linkerpagina een grote kaart van het hoofdstuk: geen lege pagina's.
            # Met een luchtfoto (bijv. Google Earth Pro-export) wordt die de linkerpagina; valt de
            # opening rechts zonder ruimte ervoor, dan komt de luchtfoto direct na de opening.
            lucht = hoofdstuk.get("luchtfoto")
            links_vrij = (len(paginas) + 1) % 2 == 0
            if links_vrij and lucht:
                paginas.append({"type": "luchtfoto", "h_idx": h_idx})
            elif links_vrij and self.locaties[h_idx]["punten"]:
                paginas.append({"type": "hoofdstukkaart", "h_idx": h_idx})
            paginas.append({"type": "titel", "hoofdstuk": hoofdstuk, "h_idx": h_idx})
            if lucht and not links_vrij:
                paginas.append({"type": "luchtfoto", "h_idx": h_idx})
            for pagina in hoofdstuk["paginas"]:
                if pagina["layout"] == "panorama":
                    # Een panorama hoort op een linkerpagina te beginnen
                    # (Blurb: pagina 1 is rechts, dus links = even).
                    if (len(paginas) + 1) % 2 == 1:
                        paginas.append({"type": "leeg"})
                    paginas.append({"type": "panorama", "kant": "links", **pagina})
                    paginas.append({"type": "panorama", "kant": "rechts", **pagina})
                else:
                    paginas.append({"type": "fotos", **pagina})
        # Colofon als allerlaatste pagina (een linkerpagina): bronnen, fotografen, rechten.
        minimum = self.data["drukker"].get("min_paginas", 20)
        while len(paginas) + 1 < minimum or (len(paginas) + 1) % 2:
            paginas.append({"type": "leeg"})
        paginas.append({"type": "colofon"})
        maximum = self.data["drukker"].get("max_paginas", 240)
        if len(paginas) > maximum:
            self.waarschuwingen.append(f"TE LANG   {len(paginas)} pagina's; deze drukker en dit papier staan er "
                                       f"hoogstens {maximum} toe. Haal foto's weg of kies een kleinere layout.")
        return paginas

    def vakken(self, pagina):
        """Vakken in inch op de pagina (inclusief afloop), met foto's."""
        if pagina["type"] == "panorama":
            # Eén beeld over de rug: rechts sluit naadloos aan op de snijlijn links.
            foto = pagina["fotos"][0]
            return [((0, 0, 2 * self.trim_b + 2 * self.afloop, self.pag_h), foto)]
        layout = LAYOUTS[pagina["layout"]]
        if len(pagina["fotos"]) != len(layout):
            sys.exit(f"Layout '{pagina['layout']}' vraagt {len(layout)} foto's, kreeg {len(pagina['fotos'])}.")
        g = LAYOUT_TUSSENRUIMTE_IN / 2
        uit = []
        for (fx, fy, fb, fh), foto in zip(layout, pagina["fotos"]):
            x0, y0 = self.afloop + fx * self.trim_b, self.afloop + fy * self.trim_h
            x1, y1 = x0 + fb * self.trim_b, y0 + fh * self.trim_h
            # Raakt de rand: doorlopen in de afloop. Anders: halve tussenruimte.
            x0 = 0 if fx == 0 else x0 + g
            y0 = 0 if fy == 0 else y0 + g
            x1 = self.pag_b if fx + fb >= 1 else x1 - g
            y1 = self.pag_h if fy + fh >= 1 else y1 - g
            uit.append(((x0, y0, x1 - x0, y1 - y0), foto))
        return uit

    # ---------- print ----------

    def maak_print(self, proef=False):
        doel = self.uit / "print"
        imgmap = doel / "img"
        imgmap.mkdir(parents=True, exist_ok=True)
        helderder = self.data["drukker"].get("print_helderheid", 1.04)
        pagina_html = []
        for nr, pagina in enumerate(self.paginas, start=1):
            pagina_html.append(self._print_pagina(nr, pagina, imgmap, helderder))
        kopieer_fonts(doel / "fonts")
        stijl = {**STANDAARD_STIJL, **self.data.get("stijl", {})}
        css = FONT_CSS.format(ext="ttf", fmt="truetype") + PRINT_CSS.format(b=self.pag_b, h=self.pag_h, afloop=self.afloop, veilig=self.afloop + self.veilig, **stijl)
        bron = doel / "album-print.html"
        bron.write_text(HTML_SKELET.format(titel=html.escape(self.data["titel"]), css=css,
                                           body="\n".join(pagina_html)), encoding="utf-8")
        pdf = doel / "album-binnenwerk.pdf"
        subprocess.run([vind_chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000",
                        f"--print-to-pdf={pdf}", bron.as_uri()],
                       check=True, capture_output=True)
        self._controleer_pdf(pdf)
        # Werklijst voor on1_brug.py: alleen foto's die ergens onder de doelresolutie zitten.
        (self.uit / "te-verbeteren.json").write_text(json.dumps(
            [{"bestand": b, "dpi": d, "factor": round(self.dpi_doel / d, 2)} for b, d in sorted(self.te_verbeteren.items())],
            ensure_ascii=False, indent=2), encoding="utf-8")
        if proef:
            self._maak_proef(doel)
            self.maak_contactvel(doel / "harmonisatie.jpg")
        return pdf

    def _print_pagina(self, nr, pagina, imgmap, helderder):
        kant = "rechts" if nr % 2 else "links"
        delen = []
        if pagina["type"] == "albumtitel":
            delen.append(f'<div class="albumtitel">{iconen.svg("veer", "icoon titelicoon")}<h1>{html.escape(self.data["titel"])}</h1>'
                         f'<p class="ondertitel">{html.escape(self.data.get("ondertitel", ""))}</p>'
                         f'<p class="maker">{html.escape(self.data.get("maker", ""))}</p>'
                         + (f'<p class="mede">Met foto\'s van {html.escape(", ".join(self.medefotografen()))}</p>'
                            if self.medefotografen() and self.credits_plek() in ("per_foto", "begin", "begin_en_eind")
                            else "") + '</div>')
        elif pagina["type"] == "colofon":
            delen.append(f'<div class="colofon">{self.colofon_html()}</div>')
        elif pagina["type"] == "overzicht":
            svg = self.overzicht_svg()
            if svg:
                lijst = "".join(f'<li><span>{n + 1:02d}</span>{iconen.svg(self.locaties[n]["icoon"], "icoon lijsticoon")}'
                                f'{html.escape(h["titel"])}'
                                f'<em>{html.escape(self.locaties[n]["korte_naam"])}</em></li>'
                                for n, h in enumerate(self.data["hoofdstukken"]))
                delen.append(f'<div class="overzicht"><p class="kicker">Waar deze foto\'s zijn gemaakt</p>'
                             f'<div class="grotekaart">{svg}</div><ol>{lijst}</ol></div>')
        elif pagina["type"] == "luchtfoto":
            h = self.data["hoofdstukken"][pagina["h_idx"]]
            foto = {"bestand": h["luchtfoto"], "focus": h.get("luchtfoto_focus", "50% 50%"), "luchtfoto": True}
            naam = self._print_foto(foto, self.pag_b, self.pag_h, imgmap, 1.0, nr)
            # Google vraagt een leesbare bronvermelding (minstens 6 pt) en geen aanpassing van het beeld:
            # daarom geen kleurcorrectie, geen extra helderheid, en de bron altijd zichtbaar.
            bron = html.escape(h.get("luchtfoto_bron", "Beeld: Google Earth"))
            delen.append(f'<img src="img/{naam}" style="left:0;top:0;width:{self.pag_b}in;height:{self.pag_h}in;'
                         f'object-position:{foto["focus"]}" alt="">'
                         f'<p class="luchtbron">{bron}</p>')
        elif pagina["type"] == "hoofdstukkaart":
            loc = self.locaties[pagina["h_idx"]]
            svg = self.kaart_svg(pagina["h_idx"], 720, 560, label=True)
            if svg:
                coord = kaart.coordinaten(*loc["midden"]) if loc["midden"] else ""
                delen.append(f'<div class="hoofdstukkaart"><div class="grotekaart">{svg}</div>'
                             f'<p class="plek">{html.escape(loc["plekregel"])}</p>'
                             f'<p class="coord">{iconen.svg("kompas", "icoon regelicoon")}{coord}</p></div>')
        elif pagina["type"] == "titel":
            h, n = pagina["hoofdstuk"], pagina["h_idx"]
            loc = self.locaties[n]
            # Staat links al de grote kaart, dan hier geen klein kaartje.
            vorige = self.paginas[nr - 2] if nr >= 2 else {}
            klein = "" if vorige.get("type") == "hoofdstukkaart" else self.kaart_svg(n)
            coord = kaart.coordinaten(*loc["midden"]) if loc["midden"] else ""
            meta = " — ".join(x for x in (coord, loc["periode"]) if x)
            delen.append(f'<div class="opening">{iconen.svg(loc["icoon"], "icoon openingsicoon")}'
                         f'<p class="kicker">Hoofdstuk {n + 1:02d}</p>'
                         f'<h2>{html.escape(h["titel"])}</h2><hr>'
                         + (f'<p class="plek">{html.escape(loc["plekregel"])}</p>' if loc["plekregel"] else "")
                         + (f'<p class="coord">{iconen.svg("kompas", "icoon regelicoon") if coord else ""}{meta}</p>'
                            if meta else "")
                         + f'<p class="intro">{html.escape(h.get("intro", ""))}</p></div>'
                         + (f'<div class="kleinekaart">{klein}</div>' if klein else ""))
        elif pagina["type"] in ("fotos", "panorama"):
            for (x, y, b, h), foto in self.vakken(pagina):
                naam = self._print_foto(foto, b, h, imgmap, helderder, nr)
                links = x if pagina["type"] != "panorama" or pagina["kant"] == "links" else x - self.trim_b
                focus = foto.get("focus", "50% 50%")
                delen.append(f'<img src="img/{naam}" style="left:{links}in;top:{y}in;width:{b}in;height:{h}in;'
                             f'object-position:{focus}" alt="">')
            bijschrift = pagina.get("bijschrift")
            credit = self.credit(pagina)
            tekst = " · ".join(x for x in (html.escape(bijschrift) if bijschrift else "", credit) if x)
            if tekst and (pagina["type"] != "panorama" or pagina["kant"] == "rechts"):
                delen.append(f'<p class="bijschrift">{tekst}</p>')
        return f'<section class="pagina {kant}" data-nr="{nr}">{"".join(delen)}</section>'

    def _print_foto(self, foto, vak_b, vak_h, imgmap, helderder, nr):
        img = self.laad(foto)
        dpi = min(img.width / vak_b, img.height / vak_h)
        label = f"pagina {nr}: {foto['bestand']}"
        if dpi < self.dpi_min:
            self.waarschuwingen.append(f"TE KLEIN  {label} haalt {dpi:.0f} dpi (minimaal {self.dpi_min}). "
                                       "Kies een kleiner vak of een andere foto.")
        elif dpi < self.dpi_doel * 0.8:
            self.waarschuwingen.append(f"MATIG    {label} haalt {dpi:.0f} dpi; acceptabel, niet ideaal.")
        if dpi < self.dpi_doel * 0.8 and not foto.get("luchtfoto"):  # Google-beeld niet laten bewerken door ON1
            self.te_verbeteren[foto["bestand"]] = min(round(dpi), self.te_verbeteren.get(foto["bestand"], 10_000))
        # Schalen naar doelresolutie voor het vak (cover), nooit opschalen.
        schaal = min(1.0, max(vak_b * self.dpi_doel / img.width, vak_h * self.dpi_doel / img.height))
        if schaal < 1:
            img = img.resize((round(img.width * schaal), round(img.height * schaal)), Image.LANCZOS)
        img = ImageEnhance.Brightness(img).enhance(helderder)
        naam = f"{Path(foto['bestand']).stem}-{round(vak_b * 100)}x{round(vak_h * 100)}.jpg"
        img.save(imgmap / naam, "JPEG", quality=92, subsampling=0,
                 icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
        return naam

    def _controleer_pdf(self, pdf):
        try:
            from pypdf import PdfReader
        except ImportError:
            return
        lezer = PdfReader(pdf)
        verwacht = (round(self.pag_b * 72, 1), round(self.pag_h * 72, 1))
        for i, p in enumerate(lezer.pages, start=1):
            maat = (round(float(p.mediabox.width), 1), round(float(p.mediabox.height), 1))
            if abs(maat[0] - verwacht[0]) > 1 or abs(maat[1] - verwacht[1]) > 1:
                self.waarschuwingen.append(f"PDF-maat pagina {i} is {maat} pt, verwacht {verwacht} pt.")
                break
        if len(lezer.pages) != len(self.paginas):
            self.waarschuwingen.append(f"PDF heeft {len(lezer.pages)} pagina's, verwacht {len(self.paginas)}.")

    def _maak_proef(self, doel):
        """Spreads naast elkaar met snij- en veiligheidslijnen, als PNG."""
        spreads = []
        # Pagina 1 staat rechts naast het schutblad.
        stukken = ["<section class='pagina links schutblad'></section>"]
        stukken += [f"<div class='kopie' data-nr='{i}'></div>" for i in range(1, len(self.paginas) + 1)]
        for i in range(0, len(stukken), 2):
            spreads.append(f"<div class='spread'>{stukken[i]}{stukken[i + 1] if i + 1 < len(stukken) else ''}</div>")
        proef = doel / "proef.html"
        proef.write_text(PROEF_HTML.format(b=self.pag_b, h=self.pag_h, afloop=self.afloop,
                                           veilig=self.afloop + self.veilig, spreads="\n".join(spreads)),
                         encoding="utf-8")
        hoogte = int((self.pag_h * 48 + 24) * len(spreads) + 24)
        subprocess.run([vind_chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--window-size={int(self.pag_b * 96 + 48)},{hoogte}", "--virtual-time-budget=20000",
                        f"--screenshot={doel / 'proef.png'}", proef.as_uri()],
                       check=True, capture_output=True)

    # ---------- web ----------

    def maak_web(self):
        doel = self.uit / "web"
        imgmap = doel / "img"
        imgmap.mkdir(parents=True, exist_ok=True)
        w = self.data.get("web", {})
        breedtes = w.get("breedtes", [640, 1280, 1920])
        basis_url = w.get("basis_url", "").rstrip("/")
        secties, schema_fotos, schema_plaatsen = [], [], []
        kopieer_fonts(doel / "fonts", web=True)
        for h_idx, hoofdstuk in enumerate(self.data["hoofdstukken"]):
            figuren = []
            for pagina in hoofdstuk["paginas"]:
                fotos = [f for f in pagina["fotos"] if not f.get("alleen_print")]
                if not fotos:
                    continue
                items = []
                for foto in fotos:
                    srcset, groot, (bw, bh) = self._web_foto(foto, breedtes, imgmap, w.get("kwaliteit", 80))
                    alt = html.escape(foto.get("alt") or foto.get("bijschrift") or "")
                    # De eerste foto is meestal het grootste element in beeld: niet uitstellen.
                    laden = 'loading="lazy"' if schema_fotos else 'fetchpriority="high"'
                    items.append(f'<img src="img/{groot}" srcset="{srcset}" sizes="(min-width: 900px) 50vw, 100vw" '
                                 f'width="{bw}" height="{bh}" alt="{alt}" {laden} decoding="async"'
                                 f' style="object-position:{foto.get("focus", "50% 50%")}">')
                    schema_fotos.append({"@type": "ImageObject", "contentUrl": f"{basis_url}/img/{groot}",
                                         "description": foto.get("alt") or foto.get("bijschrift") or "",
                                         "caption": foto.get("bijschrift", pagina.get("bijschrift", ""))})
                vorm = "panorama" if pagina["layout"] == "panorama" else f"n{len(items)}"
                onderschrift = " · ".join(x for x in (pagina.get("bijschrift") or "",
                                                     self.credit({"fotos": fotos}).replace("&amp;", "&")) if x)
                figuren.append(f'<figure class="{vorm}"><div class="beelden">{"".join(items)}</div>'
                               + (f"<figcaption>{html.escape(onderschrift)}</figcaption>" if onderschrift else "")
                               + "</figure>")
            loc = self.locaties[h_idx]
            coord = kaart.coordinaten(*loc["midden"]) if loc["midden"] else ""
            meta = " — ".join(x for x in (coord, loc["periode"]) if x)
            svg = self.kaart_svg(h_idx)
            secties.append(f'<section class="hoofdstuk" id="h{h_idx + 1}"><header class="opening">'
                           f'<div class="tekst">{iconen.svg(loc["icoon"], "icoon openingsicoon")}'
                           f'<p class="nummer">Hoofdstuk {h_idx + 1:02d}</p>'
                           f'<h2>{html.escape(hoofdstuk["titel"])}</h2><hr>'
                           + (f'<p class="plek">{html.escape(loc["plekregel"])}</p>' if loc["plekregel"] else "")
                           + (f'<p class="coord">{iconen.svg("kompas", "icoon regelicoon") if coord else ""}{meta}</p>'
                              if meta else "")
                           + f'<p class="intro">{html.escape(hoofdstuk.get("intro", ""))}</p></div>'
                           + (f'<div class="kaartje">{svg}</div>' if svg else "")
                           + f'</header>{self._web_luchtfoto(hoofdstuk, breedtes, imgmap, w)}{"".join(figuren)}</section>')
            if loc["midden"]:
                schema_plaatsen.append({"@type": "Place", "name": loc["korte_naam"] or loc["plekregel"],
                                        "geo": {"@type": "GeoCoordinates", "latitude": round(loc["midden"][1], 4),
                                                "longitude": round(loc["midden"][0], 4)}})
        schema = {"@context": "https://schema.org", "@type": "ImageGallery", "name": self.data["titel"],
                  "description": self.data.get("ondertitel", ""), "image": schema_fotos}
        if schema_plaatsen:
            schema["contentLocation"] = schema_plaatsen
        inhoud = (f'<article class="fotoalbum"><header class="album-kop"><h1>{html.escape(self.data["titel"])}</h1>'
                  f'<p>{html.escape(self.data.get("ondertitel", ""))}</p></header>{"".join(secties)}'
                  + '<footer class="bron">' + " · ".join(f"{k}: {v}" if k else v for k, v in self.colofon_regels()
                                                         if k != "Lettertype") + '</footer></article>'
                  f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>')
        # Los fragment voor plaatsing op de website, plus een volledige preview.
        web_css = FONT_CSS.format(ext="woff2", fmt="woff2") + WEB_CSS
        (doel / "album-fragment.html").write_text(f"<style>{web_css}</style>\n{inhoud}", encoding="utf-8")
        (doel / "index.html").write_text(HTML_SKELET.format(titel=html.escape(self.data["titel"]), css=web_css,
                                                            body=inhoud), encoding="utf-8")
        return doel / "index.html"

    def _web_luchtfoto(self, hoofdstuk, breedtes, imgmap, w):
        # Google Earth-beelden mogen niet commercieel of promotioneel worden gebruikt; een bedrijfssite valt
        # daar al snel onder. Daarom alleen op het web met "luchtfoto_web": true.
        if not hoofdstuk.get("luchtfoto") or not hoofdstuk.get("luchtfoto_web"):
            return ""
        foto = {"bestand": hoofdstuk["luchtfoto"], "web_naam": "lucht-" + Path(hoofdstuk["luchtfoto"]).name}
        srcset, groot, (bw, bh) = self._web_foto(foto, breedtes, imgmap, w.get("kwaliteit", 80))
        bron = html.escape(hoofdstuk.get("luchtfoto_bron", "Beeld: Google Earth"))
        return (f'<figure class="luchtfoto"><img src="img/{groot}" srcset="{srcset}" sizes="100vw" width="{bw}" '
                f'height="{bh}" alt="Luchtbeeld van {html.escape(self.locaties[self.data["hoofdstukken"].index(hoofdstuk)]["korte_naam"])}" '
                f'loading="lazy" decoding="async"><figcaption>{bron}</figcaption></figure>')

    def _web_foto(self, foto, breedtes, imgmap, kwaliteit):
        img = self.laad(foto)  # nieuw opgeslagen: geen EXIF of GPS mee
        stam = Path(foto.get("web_naam") or foto["bestand"]).stem
        delen, laatste = [], None
        for b in breedtes:
            if b > img.width and laatste:
                continue
            kopie = img if b >= img.width else img.resize((b, round(img.height * b / img.width)), Image.LANCZOS)
            naam = f"{stam}-{kopie.width}.webp"
            kopie.save(imgmap / naam, "WEBP", quality=kwaliteit, method=6)
            delen.append(f"img/{naam} {kopie.width}w")
            laatste = (naam, kopie.size)
        return ", ".join(delen), laatste[0], laatste[1]


HTML_SKELET = """<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel}</title><style>{css}</style></head><body>
{body}
</body></html>
"""

FONT_CSS = """
@font-face {{ font-family: "Cormorant Garamond"; src: url("fonts/CormorantGaramond.{ext}") format("{fmt}");
  font-weight: 300 700; font-style: normal; }}
@font-face {{ font-family: "Cormorant Garamond"; src: url("fonts/CormorantGaramond-Italic.{ext}") format("{fmt}");
  font-weight: 300 700; font-style: italic; }}
"""

PRINT_CSS = """
@page {{ size: {b}in {h}in; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: #fff; }}
body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.pagina {{ position: relative; width: {b}in; height: {h}in; overflow: hidden; break-after: page;
  background: {achtergrond}; color: {tekst}; }}
.pagina img {{ position: absolute; object-fit: cover; display: block; }}
.titelblok {{ position: absolute; left: {veilig}in; right: {veilig}in; bottom: calc({veilig}in + 0.6in); }}
.nummer {{ font: 600 11pt/1 {schreefloos}; letter-spacing: .2em; color: {accent}; margin-bottom: .25in; }}
.titelblok h2 {{ font: 400 54pt/1.02 {koppen}; letter-spacing: -.01em; max-width: 9in; }}
.intro {{ font: 400 13pt/1.55 {schreefloos}; max-width: 6.2in; margin-top: .3in; opacity: .8; }}
.bijschrift {{ position: absolute; left: {veilig}in; bottom: {veilig}in; max-width: 6in; padding: .08in .14in;
  font: 400 9.5pt/1.4 {schreefloos}; background: rgba(255,255,255,.88); color: #222; }}
.pagina.links .bijschrift {{ left: auto; right: {veilig}in; }}
.kicker {{ font: 600 8.5pt/1 {schreefloos}; letter-spacing: .32em; text-transform: uppercase; color: {accent}; }}
.albumtitel {{ position: absolute; left: calc({veilig}in + 0.6in); right: {veilig}in; top: 38%; }}
.albumtitel h1 {{ font: 300 66pt/1 {koppen}; letter-spacing: -.01em; }}
.albumtitel .ondertitel {{ font: italic 400 18pt/1.4 {koppen}; margin-top: .25in; opacity: .8; max-width: 7in; }}
.albumtitel .mede {{ font: italic 400 12pt/1.4 {koppen}; margin-top: .14in; opacity: .7; }}
.albumtitel .maker {{ font: 500 9pt/1 {schreefloos}; letter-spacing: .3em; text-transform: uppercase; margin-top: .6in; opacity: .7; }}
.opening {{ position: absolute; left: calc({veilig}in + 0.5in); top: calc({veilig}in + 1.1in); width: 6.2in; }}
.opening .kicker {{ margin-bottom: .32in; }}
.opening h2 {{ font: 300 50pt/1.02 {koppen}; letter-spacing: -.005em; }}
.opening hr {{ border: 0; border-top: .6pt solid {accent}; width: .9in; margin: .32in 0 .26in; }}
.plek {{ font: 600 8.5pt/1.5 {schreefloos}; letter-spacing: .22em; text-transform: uppercase; }}
.coord {{ font: italic 400 12pt/1.5 {koppen}; opacity: .7; margin-top: .06in; }}
.opening .intro {{ font: 400 17pt/1.5 {koppen}; margin-top: .36in; max-width: 5.4in; opacity: .9; }}
.kleinekaart {{ position: absolute; right: calc({veilig}in + 0.3in); bottom: calc({veilig}in + 0.3in); width: 4.4in; }}
.kaart {{ display: block; width: 100%; height: auto; }}
.kaartlabel, .kaartnummer {{ font-family: {schreefloos}; text-transform: uppercase; }}
.hoofdstukkaart, .overzicht {{ position: absolute; inset: calc({veilig}in + 0.4in); display: flex; flex-direction: column;
  justify-content: center; }}
.grotekaart {{ width: 100%; }}
.hoofdstukkaart .plek {{ margin-top: .3in; }}
.overzicht .kicker {{ margin-bottom: .25in; }}
.overzicht ol {{ list-style: none; columns: 2; column-gap: .5in; margin-top: .25in; }}
.overzicht li {{ font: 400 12pt/1.9 {koppen}; break-inside: avoid; }}
.overzicht li span {{ font: 600 8pt/1 {schreefloos}; letter-spacing: .15em; color: {accent}; margin-right: .14in; }}
.icoon {{ display: inline-block; color: {accent}; vertical-align: middle; }}
.titelicoon {{ width: .55in; height: .55in; margin-bottom: .35in; }}
.openingsicoon {{ display: block; width: .46in; height: .46in; margin-bottom: .28in; }}
.regelicoon {{ width: 11pt; height: 11pt; margin: -2pt 5pt 0 0; opacity: .8; }}
.lijsticoon {{ width: 12pt; height: 12pt; margin: -2pt 7pt 0 0; }}
.luchtbron {{ position: absolute; right: {veilig}in; bottom: {veilig}in; font: 400 6.5pt/1.3 {schreefloos};
  color: #fff; text-shadow: 0 0 3pt rgba(0,0,0,.6); max-width: 5in; text-align: right; }}
.pagina.rechts .luchtbron {{ right: auto; left: {veilig}in; text-align: left; }}
.colofon {{ position: absolute; left: calc({veilig}in + 0.5in); bottom: calc({veilig}in + 0.6in); width: 6in; }}
.colofon h3 {{ font: 300 22pt/1.1 {koppen}; margin: .18in 0 .3in; }}
.colofon p {{ display: flex; font: 400 9pt/1.6 {schreefloos}; margin: 0 0 .06in; }}
.colofon p span {{ flex: 0 0 1.5in; opacity: .55; }}
.colofon .recht {{ margin-top: .25in; opacity: .7; }}
.overzicht .bron {{ font: 400 7pt/1 {schreefloos}; opacity: .5; margin-top: .2in; }}
.overzicht li em {{ opacity: .6; margin-left: .1in; font-size: 10.5pt; }}
"""

PROEF_HTML = """<!doctype html><html lang="nl"><head><meta charset="utf-8"><style>
body {{ margin: 24px; background: #2b2b2b; font-family: Inter, sans-serif; }}
.spread {{ display: flex; margin-bottom: 24px; zoom: .5; }}
.spread > * {{ position: relative; width: {b}in; height: {h}in; background: #fff; overflow: hidden; }}
.schutblad {{ background: #e9e6e1 !important; }}
.spread > *::after {{ content: ""; position: absolute; inset: {afloop}in; outline: 2px solid #e5484d; pointer-events: none; z-index: 9; }}
.spread > *::before {{ content: ""; position: absolute; inset: {veilig}in; outline: 2px dashed #3e9bff; pointer-events: none; z-index: 9; }}
iframe {{ border: 0; width: {b}in; height: {h}in; }}
</style></head><body>
{spreads}
<script>
fetch('album-print.html').then(r => r.text()).then(t => {{
  const doc = new DOMParser().parseFromString(t, 'text/html');
  const css = doc.querySelector('style').textContent.replace(/@page[^}}]*}}/, '');
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  document.querySelectorAll('.kopie').forEach(el => {{
    const p = doc.querySelector('.pagina[data-nr="' + el.dataset.nr + '"]');
    if (p) el.replaceWith(document.importNode(p, true));
  }});
}});
</script></body></html>
"""

WEB_CSS = """
.fotoalbum { --tekst: #1d1c1a; --zacht: #6b675f; --accent: #b4532a; --vlak: #faf8f5;
  color: var(--tekst); background: var(--vlak); font: 400 1.0625rem/1.65 Inter, system-ui, sans-serif; }
@media (prefers-color-scheme: dark) { .fotoalbum { --tekst: #efece6; --zacht: #a9a49a; --accent: #e08a5f; --vlak: #161514; } }
.fotoalbum * { box-sizing: border-box; }
.fotoalbum .album-kop { max-width: 72rem; margin: 0 auto; padding: clamp(3rem, 8vw, 7rem) 1rem 2rem; }
.fotoalbum h1 { font: 300 clamp(2.6rem, 7vw, 5.4rem)/1.0 "Cormorant Garamond", Georgia, serif; margin: 0; letter-spacing: -.01em; }
.fotoalbum .album-kop p { color: var(--zacht); max-width: 38rem; margin: 1rem 0 0; }
.fotoalbum .hoofdstuk { max-width: 72rem; margin: 0 auto; padding: 3rem 1rem; }
.fotoalbum .hoofdstuk header { max-width: 40rem; margin-bottom: 2rem; }
.fotoalbum .nummer { font-weight: 600; font-size: .8rem; letter-spacing: .2em; color: var(--accent); margin: 0 0 .75rem; }
.fotoalbum h2 { font: 300 clamp(2.2rem, 5vw, 3.6rem)/1.02 "Cormorant Garamond", Georgia, serif; margin: 0; }
.fotoalbum .intro { color: var(--zacht); margin: 1rem 0 0; }
.fotoalbum figure { margin: 0 0 clamp(1.5rem, 4vw, 3rem); }
.fotoalbum .beelden { display: grid; gap: .5rem; min-width: 0; }
.fotoalbum img { width: 100%; height: 100%; object-fit: cover; display: block; background: #0001; }
.fotoalbum .n1 img { aspect-ratio: 13 / 11; max-height: 88vh; }
.fotoalbum .panorama img { aspect-ratio: 26 / 11; }
.fotoalbum .n2 img, .fotoalbum .n4 img { aspect-ratio: 4 / 5; }
.fotoalbum .n3 img { aspect-ratio: 4 / 3; }
@media (min-width: 900px) {
  .fotoalbum .n2 .beelden { grid-template-columns: 1fr 1fr; }
  .fotoalbum .n3 .beelden { grid-template-columns: 1.6fr 1fr; grid-template-rows: 1fr 1fr; }
  .fotoalbum .n3 img:first-child { grid-row: span 2; aspect-ratio: auto; }
  .fotoalbum .n4 .beelden { grid-template-columns: 1fr 1fr; }
  .fotoalbum .n4 img { aspect-ratio: 13 / 11; }
}
.fotoalbum .hoofdstuk header.opening { display: grid; gap: 1.5rem 3rem; align-items: end; max-width: none; }
.fotoalbum .opening .tekst { max-width: 38rem; }
.fotoalbum .opening .nummer { letter-spacing: .32em; text-transform: uppercase; font-size: .72rem; }
.fotoalbum .opening hr { border: 0; border-top: 1px solid var(--accent); width: 4.5rem; margin: 1.4rem 0 1.1rem; }
.fotoalbum .plek { font-weight: 600; font-size: .72rem; letter-spacing: .22em; text-transform: uppercase; margin: 0; }
.fotoalbum .coord { font: italic 400 1.05rem/1.5 "Cormorant Garamond", Georgia, serif; color: var(--zacht); margin: .2rem 0 0; }
.fotoalbum .opening .intro { font: 400 1.2rem/1.6 "Cormorant Garamond", Georgia, serif; color: var(--tekst); }
.fotoalbum .icoon { display: inline-block; color: var(--accent); vertical-align: middle; }
.fotoalbum .openingsicoon { display: block; width: 2.25rem; height: 2.25rem; margin-bottom: 1.1rem; }
.fotoalbum .regelicoon { width: .95rem; height: .95rem; margin: -.15rem .4rem 0 0; opacity: .8; }
.fotoalbum .kaartje { max-width: 22rem; width: 100%; }
.fotoalbum .kaart { display: block; width: 100%; height: auto; }
.fotoalbum .kaartlabel { font-family: Inter, system-ui, sans-serif; text-transform: uppercase; }
@media (min-width: 900px) { .fotoalbum .hoofdstuk header.opening { grid-template-columns: minmax(0, 38rem) 22rem; justify-content: space-between; } }
@media (prefers-color-scheme: dark) { .fotoalbum .kaart { filter: invert(.88) hue-rotate(180deg); } }
.fotoalbum .bron { max-width: 72rem; margin: 0 auto; padding: 2rem 1rem 3rem; font-size: .75rem; color: var(--zacht); }
.fotoalbum figcaption { color: var(--zacht); font-size: .9rem; margin-top: .6rem; max-width: 40rem; }
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("album")
    parser.add_argument("--alleen", choices=["print", "web"])
    parser.add_argument("--proef", action="store_true", help="maak proef.png met snij- en veiligheidslijnen")
    args = parser.parse_args()
    album = Album(args.album)
    if args.alleen != "web":
        pdf = album.maak_print(proef=args.proef)
        print(f"Print: {pdf}  ({len(album.paginas)} pagina's, {album.trim_b:.2f} x {album.trim_h:.2f} inch bijgesneden)")
        print(f"Kaft:  {kaft.maak(album, sys.modules[__name__], proef=args.proef)}")
    if args.alleen != "print":
        print(f"Web:   {album.maak_web()}")
    for regel in album.waarschuwingen:
        print("  ! " + regel)
    print("Controleer de paginamaat in Blurbs Specification Calculator voordat je uploadt." if not
          album.data["drukker"].get("maat_gecontroleerd") else "Paginamaat is gecontroleerd tegen Blurb.")


if __name__ == "__main__":
    main()
