#!/usr/bin/env python3
"""EQwise fotoalbum: één bron (album.json), twee uitvoeren.

  print/  drukklare PDF met losse pagina's voor Blurb "PDF to Book"
  web/    snelle, vindbare verhaalpagina met WebP-srcset en schema.org

Gebruik:
  python3 fotoalbum/build.py pad/naar/album.json [--alleen print|web] [--proef]

Foto's staan in de map "fotos" naast album.json (instelbaar met "fotomap").
"""

import argparse
import html
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageCms, ImageEnhance, ImageOps

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
    "koppen": "Caladea, 'Bitstream Charter', Georgia, serif",
    "schreefloos": "Inter, 'Liberation Sans', sans-serif",
}


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
        self.paginas = self._bouw_paginas()

    # ---------- inhoud naar pagina's ----------

    def _bouw_paginas(self):
        paginas = []
        for h_idx, hoofdstuk in enumerate(self.data["hoofdstukken"]):
            paginas.append({"type": "titel", "hoofdstuk": hoofdstuk, "h_idx": h_idx})
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
        if len(paginas) % 2:
            paginas.append({"type": "leeg"})
        minimum = self.data["drukker"].get("min_paginas", 20)
        while len(paginas) < minimum:
            paginas.append({"type": "leeg"})
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
        stijl = {**STANDAARD_STIJL, **self.data.get("stijl", {})}
        css = PRINT_CSS.format(b=self.pag_b, h=self.pag_h, afloop=self.afloop, veilig=self.afloop + self.veilig, **stijl)
        bron = doel / "album-print.html"
        bron.write_text(HTML_SKELET.format(titel=html.escape(self.data["titel"]), css=css,
                                           body="\n".join(pagina_html)), encoding="utf-8")
        pdf = doel / "album-binnenwerk.pdf"
        subprocess.run([vind_chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000",
                        f"--print-to-pdf={pdf}", bron.as_uri()],
                       check=True, capture_output=True)
        self._controleer_pdf(pdf)
        if proef:
            self._maak_proef(doel)
        return pdf

    def _print_pagina(self, nr, pagina, imgmap, helderder):
        kant = "rechts" if nr % 2 else "links"
        delen = []
        if pagina["type"] == "titel":
            h = pagina["hoofdstuk"]
            delen.append(f'<div class="titelblok"><p class="nummer">{pagina["h_idx"] + 1:02d}</p>'
                         f'<h2>{html.escape(h["titel"])}</h2>'
                         f'<p class="intro">{html.escape(h.get("intro", ""))}</p></div>')
        elif pagina["type"] in ("fotos", "panorama"):
            for (x, y, b, h), foto in self.vakken(pagina):
                naam = self._print_foto(foto, b, h, imgmap, helderder, nr)
                links = x if pagina["type"] != "panorama" or pagina["kant"] == "links" else x - self.trim_b
                focus = foto.get("focus", "50% 50%")
                delen.append(f'<img src="img/{naam}" style="left:{links}in;top:{y}in;width:{b}in;height:{h}in;'
                             f'object-position:{focus}" alt="">')
            bijschrift = pagina.get("bijschrift")
            if bijschrift and (pagina["type"] != "panorama" or pagina["kant"] == "rechts"):
                delen.append(f'<p class="bijschrift">{html.escape(bijschrift)}</p>')
        return f'<section class="pagina {kant}" data-nr="{nr}">{"".join(delen)}</section>'

    def _print_foto(self, foto, vak_b, vak_h, imgmap, helderder, nr):
        bron = self.fotomap / foto["bestand"]
        img = open_foto(bron)
        dpi = min(img.width / vak_b, img.height / vak_h)
        label = f"pagina {nr}: {foto['bestand']}"
        if dpi < self.dpi_min:
            self.waarschuwingen.append(f"TE KLEIN  {label} haalt {dpi:.0f} dpi (minimaal {self.dpi_min}). "
                                       "Kies een kleiner vak of een andere foto.")
        elif dpi < self.dpi_doel * 0.8:
            self.waarschuwingen.append(f"MATIG    {label} haalt {dpi:.0f} dpi; acceptabel, niet ideaal.")
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
        secties, schema_fotos = [], []
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
                onderschrift = pagina.get("bijschrift")
                figuren.append(f'<figure class="{vorm}"><div class="beelden">{"".join(items)}</div>'
                               + (f"<figcaption>{html.escape(onderschrift)}</figcaption>" if onderschrift else "")
                               + "</figure>")
            secties.append(f'<section class="hoofdstuk" id="h{h_idx + 1}"><header><p class="nummer">'
                           f'{h_idx + 1:02d}</p><h2>{html.escape(hoofdstuk["titel"])}</h2>'
                           f'<p class="intro">{html.escape(hoofdstuk.get("intro", ""))}</p></header>'
                           f'{"".join(figuren)}</section>')
        schema = {"@context": "https://schema.org", "@type": "ImageGallery", "name": self.data["titel"],
                  "description": self.data.get("ondertitel", ""), "image": schema_fotos}
        inhoud = (f'<article class="fotoalbum"><header class="album-kop"><h1>{html.escape(self.data["titel"])}</h1>'
                  f'<p>{html.escape(self.data.get("ondertitel", ""))}</p></header>{"".join(secties)}</article>'
                  f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>')
        # Los fragment voor plaatsing op de website, plus een volledige preview.
        (doel / "album-fragment.html").write_text(f"<style>{WEB_CSS}</style>\n{inhoud}", encoding="utf-8")
        (doel / "index.html").write_text(HTML_SKELET.format(titel=html.escape(self.data["titel"]), css=WEB_CSS,
                                                            body=inhoud), encoding="utf-8")
        return doel / "index.html"

    def _web_foto(self, foto, breedtes, imgmap, kwaliteit):
        img = open_foto(self.fotomap / foto["bestand"])  # nieuw opgeslagen: geen EXIF of GPS mee
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
.fotoalbum h1 { font: 400 clamp(2.4rem, 6vw, 4.8rem)/1.02 Caladea, Charter, Georgia, serif; margin: 0; letter-spacing: -.01em; }
.fotoalbum .album-kop p { color: var(--zacht); max-width: 38rem; margin: 1rem 0 0; }
.fotoalbum .hoofdstuk { max-width: 72rem; margin: 0 auto; padding: 3rem 1rem; }
.fotoalbum .hoofdstuk header { max-width: 40rem; margin-bottom: 2rem; }
.fotoalbum .nummer { font-weight: 600; font-size: .8rem; letter-spacing: .2em; color: var(--accent); margin: 0 0 .75rem; }
.fotoalbum h2 { font: 400 clamp(1.8rem, 4vw, 3rem)/1.08 Caladea, Charter, Georgia, serif; margin: 0; }
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
    if args.alleen != "print":
        print(f"Web:   {album.maak_web()}")
    for regel in album.waarschuwingen:
        print("  ! " + regel)
    print("Controleer de paginamaat in Blurbs Specification Calculator voordat je uploadt." if not
          album.data["drukker"].get("maat_gecontroleerd") else "Paginamaat is gecontroleerd tegen Blurb.")


if __name__ == "__main__":
    main()
