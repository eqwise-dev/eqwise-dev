"""Kaft voor Blurb ImageWrap (hardcover met bedrukte omslag): één PDF met
achterkant, rug en voorkant naast elkaar, plus omslagrand rondom.

    [omslag][ achterkant ][rug][ voorkant ][omslag]     hoogte: omslag + paneel + omslag

De maten hangen af van het aantal pagina's (rugdikte) en het type kaft. Neem
ze over uit Blurbs Specification Calculator in album.json → "kaft". Tot dan
rekent het script met een SCHATTING en zegt dat er luid bij.

Twee stijlen ("stijl"):
  beeld          voorkant volledig gevuld met de sterkste foto, titel klein en rustig
  passe-partout  papierkleur met één foto in een ruime marge, titel eronder;
                 de klassieke fine-art-kaft
"""

import html
import subprocess

import iconen

# Schatting voor Blurb Large Landscape ImageWrap; vervangen door de calculatorwaarden.
SCHATTING = {"paneel_breedte_in": 13.25, "paneel_hoogte_in": 11.25, "omslag_in": 0.75,
             "scharnier_in": 0.4, "rug_basis_in": 0.25, "rug_per_pagina_in": 0.0025}


def maten(album):
    k = {**SCHATTING, **album.data.get("kaft", {})}
    rug = k.get("rug_in") or round(k["rug_basis_in"] + k["rug_per_pagina_in"] * len(album.paginas), 3)
    totaal_b = 2 * k["omslag_in"] + 2 * k["paneel_breedte_in"] + rug
    totaal_h = 2 * k["omslag_in"] + k["paneel_hoogte_in"]
    return {**k, "rug_in": rug, "totaal_b": totaal_b, "totaal_h": totaal_h,
            "geschat": not album.data.get("kaft", {}).get("maat_gecontroleerd")}


def kies_voorfoto(album):
    k = album.data.get("kaft", {})
    if k.get("voor"):
        return {"bestand": k["voor"], "focus": k.get("voor_focus", "50% 50%")}
    # Anders: de eerste volle pagina of panorama, de art director koos die als sterkst.
    for hoofdstuk in album.data["hoofdstukken"]:
        for pagina in hoofdstuk["paginas"]:
            if pagina["layout"] in ("vol", "panorama"):
                return pagina["fotos"][0]
    return album.data["hoofdstukken"][0]["paginas"][0]["fotos"][0]


def maak(album, hulp, proef=False):
    m = maten(album)
    doel = album.uit / "print"
    imgmap = doel / "img"
    imgmap.mkdir(parents=True, exist_ok=True)
    hulp.kopieer_fonts(doel / "fonts")
    k = album.data.get("kaft", {})
    stijl_naam = k.get("stijl", "beeld")
    stijl = {**hulp.STANDAARD_STIJL, **album.data.get("stijl", {})}
    o, pb, ph, rug = m["omslag_in"], m["paneel_breedte_in"], m["paneel_hoogte_in"], m["rug_in"]
    voor_x = o + pb + rug  # linkerrand van de voorkant

    foto = kies_voorfoto(album)
    if stijl_naam == "beeld":
        # Foto loopt door tot over de omslagrand, maar stopt bij de rug.
        vak = (voor_x, 0, pb + o, m["totaal_h"])
    else:
        vak = (voor_x + 1.4, o + 1.1, pb - 2.8, ph * 0.56)
    naam = album._print_foto(foto, vak[2], vak[3], imgmap, album.data["drukker"].get("print_helderheid", 1.04), "kaft")

    titel = html.escape(album.data["titel"])
    ondertitel = html.escape(album.data.get("ondertitel", ""))
    maker = html.escape(album.data.get("maker", ""))
    achtertekst = html.escape(k.get("achtertekst", ""))
    veilig = 0.5  # binnen het paneel, weg van snijrand en scharnier

    voor_tekst = (f'<div class="voor-tekst">{iconen.svg("veer", "icoon kaft-icoon")}<h1>{titel}</h1>'
                  + (f'<p class="voor-onder">{ondertitel}</p>' if ondertitel and stijl_naam != "beeld" else "")
                  + (f'<p class="voor-maker">{maker}</p>' if maker else "") + "</div>")
    overzicht = album.overzicht_svg(420, 300) if k.get("kaart_achter", True) else ""
    rug_richting = k.get("rug_richting", "omhoog")  # omhoog = Europees, omlaag = Engels/Amerikaans

    css = hulp.FONT_CSS.format(ext="ttf", fmt="truetype") + KAFT_CSS.format(
        b=m["totaal_b"], h=m["totaal_h"], o=o, pb=pb, ph=ph, rug=rug, voor_x=voor_x, veilig=veilig,
        scharnier=m["scharnier_in"], vak_x=vak[0], vak_y=vak[1], vak_b=vak[2], vak_h=vak[3],
        focus=foto.get("focus", "50% 50%"), rotatie="-90deg" if rug_richting == "omhoog" else "90deg",
        donker="#1d1c1a", **stijl)
    body = (f'<section class="kaft {stijl_naam}">'
            f'<img class="voorfoto" src="img/{naam}" alt="">'
            + ('<div class="verloop"></div>' if stijl_naam == "beeld" else "")
            + voor_tekst
            + f'<div class="rug"><div class="rug-regel"><span>{titel}</span>{"<em>" + maker + "</em>" if maker else ""}</div></div>'
            + f'<div class="achter">'
            + (f'<p class="achter-tekst">{achtertekst}</p>' if achtertekst else "")
            + (f'<div class="achter-kaart">{overzicht}</div>' if overzicht else "")
            + f'<p class="bron">{hulp.KAARTBRON if overzicht else ""}</p></div>'
            + "</section>")
    bron = doel / "album-kaft.html"
    bron.write_text(hulp.HTML_SKELET.format(titel=titel + " (kaft)", css=css, body=body), encoding="utf-8")
    pdf = doel / "album-kaft.pdf"
    subprocess.run([hulp.vind_chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000",
                    f"--print-to-pdf={pdf}", bron.as_uri()], check=True, capture_output=True)
    if m["geschat"]:
        album.waarschuwingen.append(
            f"KAFT     maten zijn een SCHATTING (rug {rug:.3f} inch bij {len(album.paginas)} pagina's). Neem de "
            "waarden over uit Blurbs Specification Calculator in album.json → kaft, met maat_gecontroleerd: true.")
    if proef:
        _proef(album, hulp, doel, m, bron)
    return pdf


def _proef(album, hulp, doel, m, bron):
    """Kaft met hulplijnen: rood = snijrand, oranje = rug, blauw gestippeld = veilige zone."""
    o, pb, ph, rug, sch = m["omslag_in"], m["paneel_breedte_in"], m["paneel_hoogte_in"], m["rug_in"], m["scharnier_in"]
    lijnen = (f'<div style="position:absolute;left:{o}in;top:{o}in;width:{2 * pb + rug}in;height:{ph}in;'
              f'outline:3px solid #e5484d"></div>'
              f'<div style="position:absolute;left:{o + pb}in;top:0;width:{rug}in;height:{m["totaal_h"]}in;'
              f'background:rgba(255,140,0,.25);outline:2px solid #ff8c00"></div>')
    for x in (o + 0.5, o + pb + rug + sch):
        lijnen += (f'<div style="position:absolute;left:{x}in;top:{o + 0.5}in;width:{pb - 0.5 - sch}in;'
                   f'height:{ph - 1}in;outline:2px dashed #3e9bff"></div>')
    tekst = bron.read_text(encoding="utf-8").replace("</section>", lijnen + "</section>")
    proefbron = doel / "kaft-proef.html"
    proefbron.write_text(tekst, encoding="utf-8")
    subprocess.run([hulp.vind_chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={int(m['totaal_b'] * 96)},{int(m['totaal_h'] * 96) + 120}", "--virtual-time-budget=20000",
                    f"--screenshot={doel / 'kaft-proef.png'}", proefbron.as_uri()], check=True, capture_output=True)


KAFT_CSS = """
@page {{ size: {b}in {h}in; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.kaft {{ position: relative; width: {b}in; height: {h}in; overflow: hidden; background: {achtergrond}; color: {tekst}; }}
.icoon {{ display: inline-block; color: {accent}; }}
.voorfoto {{ position: absolute; left: {vak_x}in; top: {vak_y}in; width: {vak_b}in; height: {vak_h}in;
  object-fit: cover; object-position: {focus}; }}
.voor-tekst {{ position: absolute; left: calc({voor_x}in + {scharnier}in + {veilig}in); right: calc({o}in + {veilig}in); }}
.voor-tekst h1 {{ font: 300 44pt/1.02 {koppen}; letter-spacing: -.005em; }}
.voor-onder {{ font: italic 400 14pt/1.4 {koppen}; margin-top: .14in; opacity: .8; }}
.voor-maker {{ font: 500 8pt/1 {schreefloos}; letter-spacing: .3em; text-transform: uppercase; margin-top: .3in; opacity: .75; }}
.kaft-icoon {{ width: .4in; height: .4in; margin-bottom: .22in; }}
/* Beeld: titel onderaan op een zacht verloop, wit; geen blok, geen kader. */
.beeld .verloop {{ position: absolute; left: {voor_x}in; bottom: 0; width: calc({pb}in + {o}in); height: 45%;
  background: linear-gradient(to top, rgba(10,10,8,.55), rgba(10,10,8,0)); }}
.beeld .voor-tekst {{ bottom: calc({o}in + {veilig}in + .2in); color: #fff; }}
.beeld .kaft-icoon {{ color: #fff; opacity: .85; }}
/* Passe-partout: foto in ruime marge, titel eronder in donkere tekst. */
.passe-partout .voor-tekst {{ top: calc({vak_y}in + {vak_h}in + .45in); left: {vak_x}in; }}
.rug {{ position: absolute; left: calc({o}in + {pb}in); top: 0; width: {rug}in; height: {h}in; }}
/* Eén gedraaide regel over de lengte van de rug: titel aan het ene eind, maker aan het andere. */
.rug-regel {{ position: absolute; left: 50%; top: 50%; width: {ph}in; height: {rug}in; padding: 0 1.1in;
  transform: translate(-50%, -50%) rotate({rotatie}); display: flex; align-items: center;
  justify-content: space-between; white-space: nowrap; }}
.rug span {{ font: 400 11pt/1 {koppen}; letter-spacing: .04em; }}
.rug em {{ font: 500 6.5pt/1 {schreefloos}; letter-spacing: .25em; text-transform: uppercase; font-style: normal; opacity: .7; }}
.achter {{ position: absolute; left: calc({o}in + {veilig}in); top: calc({o}in + {veilig}in);
  width: calc({pb}in - 2 * {veilig}in - {scharnier}in); height: calc({ph}in - 2 * {veilig}in);
  display: flex; flex-direction: column; justify-content: flex-end; }}
.achter-tekst {{ font: 400 14pt/1.55 {koppen}; max-width: 6.2in; margin-bottom: .5in; }}
.achter-kaart {{ width: 4.6in; opacity: .95; }}
.kaart {{ display: block; width: 100%; height: auto; }}
.kaartnummer {{ font-family: {schreefloos}; }}
.bron {{ font: 400 6pt/1 {schreefloos}; opacity: .45; margin-top: .15in; }}
"""
