#!/usr/bin/env python3
"""Render a clean vendor-reference illustration of the purchased G-65 O-ring."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "assets" / "renders" / "revb-jlcmc-g65-oring.png"

scale = 3
width, height = 1200 * scale, 800 * scale
image = Image.new("RGBA", (width, height), (255, 255, 255, 0))

# Soft contact shadow under the ring.
shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.ellipse((210 * scale, 325 * scale, 990 * scale, 665 * scale), fill=(0, 0, 0, 55))
shadow = shadow.filter(ImageFilter.GaussianBlur(28 * scale))
image.alpha_composite(shadow)

# Build the toroidal appearance as nested elliptical bands.  The nominal
# geometry is G-65: ID 64.4 mm, section 3.1 mm, nominal OD 70.6 mm.
draw = ImageDraw.Draw(image)
outer = (205 * scale, 180 * scale, 995 * scale, 620 * scale)
inner = (275 * scale, 226 * scale, 925 * scale, 566 * scale)
draw.ellipse(outer, fill=(21, 23, 22, 255))
draw.ellipse(inner, fill=(255, 255, 255, 0))

# Specular edge and reflected lower rim make the round 3.1 mm section legible.
draw.arc(outer, 193, 347, fill=(3, 4, 3, 255), width=17 * scale)
draw.arc(outer, 12, 174, fill=(77, 82, 78, 255), width=9 * scale)
draw.arc(inner, 194, 348, fill=(52, 56, 53, 255), width=10 * scale)
draw.arc(inner, 12, 174, fill=(112, 118, 113, 255), width=7 * scale)
draw.arc((230 * scale, 198 * scale, 970 * scale, 596 * scale), 200, 338,
         fill=(7, 8, 7, 205), width=13 * scale)
draw.arc((230 * scale, 198 * scale, 970 * scale, 596 * scale), 25, 155,
         fill=(126, 132, 127, 135), width=5 * scale)

# Preserve a genuinely transparent center after antialiasing/downsampling.
image = image.resize((1200, 800), Image.Resampling.LANCZOS)
OUT.parent.mkdir(parents=True, exist_ok=True)
image.save(OUT)
print(OUT)
