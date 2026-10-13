"""
EQwise EAA-quickscan — rapport maken.

Vult template.html met de gegevens uit een JSON-bestand en schrijft een
HTML-rapport. Met --pdf wordt er ook een A4-PDF van gemaakt via Chrome of
Chromium (headless).

Gebruik:
    python render.py voorbeeld.json
    python render.py klant.json --pdf
    python render.py klant.json --pdf --uit rapporten/
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

HIER = Path(__file__).resolve().parent

VERPLICHT = {
    "rapport": ["soort", "datum", "norm", "kenmerk"],
    "klant": ["naam", "website", "website_kort"],
    "eaa": ["valt_onder", "toelichting"],
    "oordeel": ["niveau", "kop", "samenvatting"],
    "scope": ["paginas", "methoden"],
    "seo_geo": ["tekst", "punten"],
    "afzender": ["naam", "functie", "email", "telefoon", "website"],
}
KEUZES = {
    "eaa.valt_onder": {"ja", "waarschijnlijk", "nee", "onbekend"},
    "oordeel.niveau": {"rood", "oranje", "groen"},
    "bevinding.ernst": {"hoog", "middel", "laag"},
    "bevinding.inspanning": {"klein", "middel", "groot"},
    "principe.status": {"rood", "oranje", "groen"},
    "check.resultaat": {"voldoet", "deels", "voldoet niet"},
}
ERNST_VOLGORDE = {"hoog": 0, "middel": 1, "laag": 2}

CHROME_KANDIDATEN = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
]


def controleer(data: dict) -> list[str]:
    fouten = []
    for blok, velden in VERPLICHT.items():
        if blok not in data:
            fouten.append(f"Blok '{blok}' ontbreekt")
            continue
        for veld in velden:
            if veld not in data[blok]:
                fouten.append(f"Veld '{blok}.{veld}' ontbreekt")

    def keuze(pad, waarde):
        if waarde not in KEUZES[pad]:
            fouten.append(f"'{pad}' is '{waarde}', moet een van {sorted(KEUZES[pad])} zijn")

    if "eaa" in data:
        keuze("eaa.valt_onder", data["eaa"].get("valt_onder"))
    if "oordeel" in data:
        keuze("oordeel.niveau", data["oordeel"].get("niveau"))

    bevindingen = data.get("bevindingen", [])
    if not bevindingen:
        fouten.append("Geen bevindingen opgegeven")
    if len(bevindingen) > 5:
        fouten.append(f"{len(bevindingen)} bevindingen; een quickscan toont er maximaal 5")
    for i, b in enumerate(bevindingen, 1):
        for veld in ["titel", "ernst", "wcag", "wie", "waar", "wat_we_zagen", "oplossing", "inspanning"]:
            if veld not in b:
                fouten.append(f"Bevinding {i}: veld '{veld}' ontbreekt")
        keuze("bevinding.ernst", b.get("ernst"))
        keuze("bevinding.inspanning", b.get("inspanning"))
    for p in data.get("principes", []):
        keuze("principe.status", p.get("status"))
    for c in data.get("handmatige_checks", []):
        keuze("check.resultaat", c.get("resultaat"))
    if not data.get("handmatige_checks"):
        fouten.append("Geen handmatige controles opgegeven; elk rapport moet door een mens gecontroleerd zijn")
    return fouten


def vind_chrome() -> str | None:
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    for naam in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]:
        pad = shutil.which(naam)
        if pad:
            return pad
    for pad in CHROME_KANDIDATEN:
        if Path(pad).exists():
            return pad
    return None


def maak_pdf(html_pad: Path, pdf_pad: Path) -> None:
    chrome = vind_chrome()
    if not chrome:
        sys.exit("Chrome/Chromium niet gevonden. Zet CHROME_PATH, of open de HTML en kies Afdrukken > Opslaan als PDF.")
    subprocess.run(
        [
            chrome, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer", "--generate-pdf-document-outline",
            "--virtual-time-budget=5000",
            f"--print-to-pdf={pdf_pad}", html_pad.as_uri(),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Maak een EQwise EAA-quickscanrapport")
    parser.add_argument("json", type=Path, help="JSON-bestand met de scangegevens")
    parser.add_argument("--pdf", action="store_true", help="maak ook een PDF")
    parser.add_argument("--uit", type=Path, default=None, help="uitvoermap (standaard: naast het JSON-bestand)")
    args = parser.parse_args()

    data = json.loads(args.json.read_text(encoding="utf-8"))
    fouten = controleer(data)
    if fouten:
        print("Het JSON-bestand is niet compleet:", file=sys.stderr)
        for f in fouten:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)

    data["bevindingen"] = sorted(data["bevindingen"], key=lambda b: ERNST_VOLGORDE[b["ernst"]])

    env = Environment(loader=FileSystemLoader(HIER), autoescape=True, undefined=StrictUndefined)
    html = env.get_template("template.html").render(**data)

    uitmap = args.uit or args.json.resolve().parent
    uitmap.mkdir(parents=True, exist_ok=True)
    basis = f"quickscan-{data['rapport']['kenmerk']}"
    html_pad = uitmap / f"{basis}.html"
    html_pad.write_text(html, encoding="utf-8")
    print(f"HTML: {html_pad}")

    if args.pdf:
        pdf_pad = uitmap / f"{basis}.pdf"
        maak_pdf(html_pad, pdf_pad)
        print(f"PDF:  {pdf_pad}")


if __name__ == "__main__":
    main()
