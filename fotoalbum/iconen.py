"""Kleine lijniconen die de tekst begeleiden: één dunne lijn, accentkleur, spaarzaam.

Alle iconen staan op een raster van 24x24 en gebruiken currentColor, zodat ze
de kleur van de omringende tekst of het accent overnemen. Per hoofdstuk kiest
het script een leefgebied-icoon op trefwoorden; in album.json kan "icoon" dat
overschrijven ("geen" zet het uit).
"""

PADEN = {
    # Ornament en algemeen
    "veer": "M19 3C11 4 6.5 9.5 6 18M19 3c-1 6-4.5 11-13 15M5 21l1-3M9.5 14.5h4.5M8 11.5h5.5M10.5 8.5h4",
    "kompas": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 6.5l2 5.5-2 5.5-2-5.5z",
    "vogel": "M3 11c2.5-2.5 5.5-2.5 9 1 3.5-3.5 6.5-3.5 9-1",
    # Leefgebieden
    "kust": "M2 9c2.5-2 5-2 7.5 0s5 2 7.5 0 3.5-1.6 5-.6M2 14c2.5-2 5-2 7.5 0s5 2 7.5 0 3.5-1.6 5-.6M2 19c2.5-2 5-2 7.5 0s5 2 7.5 0",
    "duin": "M2 18c3-5 6-7 9-7s5 3 7 3 3-1 4-2M2 21h20M7 12.5c1-2.5 2.5-4 4-5",
    "bos": "M8 3l4.5 6.5H10l4 5.5H4l4-5.5H5.5zM9 15v5M16.5 7l3.5 5h-2l3 4h-8M17.5 16v4",
    "water": ("M3 16c2.5-1.6 5-1.6 7.5 0s5 1.6 7.5 0 2.5-1 3-.8M4 20c2.3-1.4 4.7-1.4 7 0s4.7 1.4 7 0"
              "M8 13V3.5M12 13V6.5M16 13V4.5M7.2 5.2a.8.8 0 0 1 1.6 0v3a.8.8 0 0 1-1.6 0zM15.2 6.2a.8.8 0 0 1 1.6 0v3a.8.8 0 0 1-1.6 0z"),
    "heide": "M3 20c1.5-3 3-4.5 5-4.5s3 1.5 4 1.5 2.5-2 4.5-2 3.5 2 4.5 5M7 15.5c0-2 1-3 2-3M12 17c0-3 1-5 2.5-6M16.5 15c.5-1.5 1.5-2.5 3-3",
    "berg": "M2 20l7.5-12 4 6 2.5-3.5L22 20zM8 10.5l1.5 1 1.5-1",
    "savanne": "M3 9.5c4-2.5 14-2.5 18 0M12 9.5V21M12 14l-4-4.2M12 13l3.5-3.3M5 21h14",
    "ijs": "M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M10 4.5l2 1.5 2-1.5M10 19.5l2-1.5 2 1.5",
}

# Trefwoorden (in kleine letters) per leefgebied; de eerste treffer wint.
TREFWOORDEN = [
    # Oost-Afrika eerst: parknamen zijn specifieker dan algemene woorden als "meer" of "berg".
    ("berg", ["kilimanjaro", "meru", "usambara", "uluguru", "udzungwa"]),
    ("kust", ["zanzibar", "pemba", "mafia", "indische oceaan"]),
    ("water", ["natron", "eyasi", "victoriameer", "tanganyika", "momella", "rufiji"]),
    ("savanne", ["savanne", "savanna", "wildpark", "game reserve", "safari", "serengeti", "ngorongoro", "tarangire",
                 "manyara", "ruaha", "selous", "nyerere", "mikumi", "katavi", "ndutu", "kruger", "masai", "maasai",
                 "okavango", "mara"]),
    ("berg", ["berg", "gebergte", "alpen", "pyreneeën", "mountain", "hooggebergte", "fjell"]),
    # Niet "ijs": dan wordt elke ijsvogel een sneeuwvlok.
    ("ijs", ["sneeuw", "gletsjer", "arctisch", "poolgebied", "spitsbergen", "svalbard", "toendra"]),
    ("kust", ["kust", "zee", "strand", "wad", "texel", "eiland", "klif", "haven", "baai"]),
    ("duin", ["duin", "duinen"]),
    ("water", ["meer", "plas", "rivier", "moeras", "riet", "uiterwaard", "polder", "delta", "biesbosch", "water"]),
    ("heide", ["heide", "veluwe", "drenthe"]),
    ("bos", ["bos", "woud", "forest", "park"]),
]


def kies(*teksten):
    tekst = " ".join(t for t in teksten if t).lower()
    for icoon, woorden in TREFWOORDEN:
        if any(w in tekst for w in woorden):
            return icoon
    return "veer"


def svg(naam, klasse="icoon", lijn=1.1, titel=None):
    """Inline SVG; maat bepaal je met CSS (width/height op de klasse)."""
    if not naam or naam == "geen" or naam not in PADEN:
        return ""
    label = f'<title>{titel}</title>' if titel else ""
    aria = 'role="img"' if titel else 'aria-hidden="true"'
    return (f'<svg class="{klasse}" viewBox="0 0 24 24" {aria} fill="none" stroke="currentColor" '
            f'stroke-width="{lijn}" stroke-linecap="round" stroke-linejoin="round" '
            f'xmlns="http://www.w3.org/2000/svg">{label}<path d="{PADEN[naam]}"/></svg>')


def staal(pad):
    """Overzicht van alle iconen als HTML-pagina, om de set te beoordelen."""
    tegels = "".join(f'<figure>{svg(n)}<figcaption>{n}</figcaption></figure>' for n in PADEN)
    pad.write_text(f"""<!doctype html><html lang="nl"><head><meta charset="utf-8"><title>Iconen</title><style>
body{{margin:40px;background:#faf8f5;color:#b4532a;font:13px Inter,sans-serif}}
main{{display:grid;grid-template-columns:repeat(4,140px);gap:28px}}figure{{margin:0;text-align:center}}
.icoon{{width:56px;height:56px}}figcaption{{color:#5c564c;margin-top:8px;letter-spacing:.12em;text-transform:uppercase;font-size:10px}}
</style></head><body><main>{tegels}</main></body></html>""", encoding="utf-8")
