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
        teken.ellipse([b * 0.4, h * 0.25, b * 0.6, h * 0.25 + b * 0.2], fill="#ffffffaa", outline="#fff", width=12)
        teken.text((b / 2, h * 0.8), f"{naam}  {b}x{h}", font=font, fill="white", anchor="mm")
        img.save(MAP / naam, quality=90)
    print(f"{len(FOTOS)} testbeelden in {MAP}")


if __name__ == "__main__":
    main()
