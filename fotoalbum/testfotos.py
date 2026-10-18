#!/usr/bin/env python3
"""Maakt testbeelden in voorbeeld/fotos om de albummachine zonder echte foto's te proberen."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MAP = Path(__file__).parent / "voorbeeld" / "fotos"
FOTOS = {
    "strand.jpg": ((4032, 3024), ("#f2b880", "#3b6e8f")),
    "duinen.jpg": ((4032, 3024), ("#e8d3a8", "#7a8f5b")),
    "portret.jpg": ((3024, 4032), ("#d9a5a0", "#4a3b52")),
    "markt.jpg": ((4032, 3024), ("#f4d35e", "#ee964b")),
    "haven.jpg": ((4032, 3024), ("#9fc5e8", "#1c3d5a")),
    "avond.jpg": ((4032, 3024), ("#f28f3b", "#2d1e2f")),
    "panorama.jpg": ((9000, 3000), ("#ffd6a5", "#355c7d")),
    "oud-telefoontje.jpg": ((1600, 1200), ("#cccccc", "#555555")),
    # Vogelscènes op grijze achtergrond: de bewerkte bepaalt de stijl,
    # de andere twee zijn te donker/blauw en te licht/groen.
    "bewerkt/reiger.jpg": ((4032, 3024), ("#c9c2b6", "#8f877a")),
    "reiger-donker.jpg": ((4032, 3024), ("#6f7889", "#3c4352")),
    "reiger-licht.jpg": ((4032, 3024), ("#e6ece2", "#b5bdaf")),
}


def main():
    MAP.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 160)
    for naam, ((b, h), (boven, onder)) in FOTOS.items():
        img = Image.new("RGB", (b, h))
        a, z = Image.new("RGB", (1, 1), boven).getpixel((0, 0)), Image.new("RGB", (1, 1), onder).getpixel((0, 0))
        teken = ImageDraw.Draw(img)
        for y in range(h):
            t = y / h
            teken.line([(0, y), (b, y)], fill=tuple(round(a[i] + (z[i] - a[i]) * t) for i in range(3)))
        if "reiger" in naam:
            # Een verzadigde "vogel": die kleur mag de kleurmeting niet beïnvloeden.
            teken.ellipse([b * 0.35, h * 0.3, b * 0.65, h * 0.7], fill="#e8742a")
            teken.ellipse([b * 0.58, h * 0.36, b * 0.61, h * 0.40], fill="#111")
        else:
            teken.ellipse([b * 0.4, h * 0.25, b * 0.6, h * 0.25 + b * 0.2], fill="#ffffffaa", outline="#fff", width=12)
        teken.text((b / 2, h * 0.8), f"{naam}  {b}x{h}", font=font, fill="white", anchor="mm")
        (MAP / naam).parent.mkdir(parents=True, exist_ok=True)
        img.save(MAP / naam, quality=90)
    print(f"{len(FOTOS)} testbeelden in {MAP}")


if __name__ == "__main__":
    main()
