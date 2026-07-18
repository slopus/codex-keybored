#!/usr/bin/env python3
"""Render the CM2-002 laser-marking placement/approval sheet."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


PACKAGE = Path(sys.argv[1] if len(sys.argv) > 1 else "cnc/vendor_response/2026-07-18_JLCCNC_laser_marking")
GEOMETRY = json.loads((PACKAGE / "CM2-002_LASER_GEOMETRY_RevB.json").read_text())
OUT = PACKAGE / "CM2-002_LASER_PLACEMENT_APPROVAL_RevB.pdf"
PNG_NOTE = PACKAGE / "CM2-002_LASER_PLACEMENT_PREVIEW_RevB.png"

PAGE = landscape(A4)
W, H = PAGE
INK = colors.HexColor("#11130f")
ACID = colors.HexColor("#a7d528")
SILVER = colors.HexColor("#d9ddd4")
GRID = colors.HexColor("#c9cdc3")
PALE = colors.HexColor("#f4f6ef")
RED = colors.HexColor("#ba2e1f")

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
font_regular = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
font_bold = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
if font_regular.exists() and font_bold.exists():
    pdfmetrics.registerFont(TTFont("LaserArial", str(font_regular)))
    pdfmetrics.registerFont(TTFont("LaserArialBold", str(font_bold)))
    FONT = "LaserArial"
    FONT_BOLD = "LaserArialBold"


def text(c: Canvas, x: float, y: float, value: str, size: float = 8, bold: bool = False, color=INK):
    c.setFillColor(color)
    c.setFont(FONT_BOLD if bold else FONT, size)
    c.drawString(x, y, value)


def bullet(c: Canvas, x: float, y: float, value: str, color=INK):
    c.setFillColor(ACID)
    c.circle(x + 1.4 * mm, y + 1.1 * mm, 0.9 * mm, fill=1, stroke=0)
    text(c, x + 5 * mm, y, value, 8.3, color=color)


def draw_marking_path(c: Canvas, cx: float, cy: float):
    path = c.beginPath()
    for artwork in GEOMETRY["artwork"]:
        for contour in artwork["contours"]:
            if len(contour) < 3:
                continue
            path.moveTo(cx + contour[0]["x"] * mm, cy + contour[0]["y"] * mm)
            for point in contour[1:]:
                path.lineTo(cx + point["x"] * mm, cy + point["y"] * mm)
            path.close()
    c.setFillColor(SILVER)
    c.drawPath(path, fill=1, stroke=0, fillMode=0)


c = Canvas(str(OUT), pagesize=PAGE, pageCompression=1)
c.setTitle("CM2-002 Laser Marking Placement Approval Rev B")
c.setAuthor("CODEX KEYBORED / Happy Engineering")
c.setFillColor(PALE)
c.rect(0, 0, W, H, fill=1, stroke=0)

c.setFillColor(INK)
c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
text(c, 14 * mm, H - 11 * mm, "CODEX KEYBORED / JLCCNC RESPONSE", 9, True, ACID)
text(c, 14 * mm, H - 22 * mm, "CM2-002  LASER MARKING PLACEMENT APPROVAL", 19, True, colors.white)
text(c, W - 62 * mm, H - 11 * mm, "REV B · 2026-07-18 · mm", 8, True, colors.white)
text(c, W - 62 * mm, H - 19 * mm, "SCALE 1:1 · UNDERSIDE VIEW", 8, color=colors.white)

cx, cy = 67 * mm, 94 * mm
c.setFillColor(INK)
c.setStrokeColor(colors.black)
c.setLineWidth(0.5)
c.circle(cx, cy, 47 * mm, fill=1, stroke=1)
c.setStrokeColor(colors.HexColor("#555a52"))
c.setLineWidth(0.3)
c.circle(cx, cy, 35.55 * mm, fill=0, stroke=1)
c.circle(cx, cy, 31.95 * mm, fill=0, stroke=1)
for hx, hy in ((-41, 0), (41, 0), (0, -41), (0, 41)):
    c.setFillColor(colors.HexColor("#090a08"))
    c.setStrokeColor(colors.HexColor("#777c73"))
    c.circle(cx + hx * mm, cy + hy * mm, 2.5 * mm, fill=1, stroke=1)
draw_marking_path(c, cx, cy)

c.setStrokeColor(ACID)
c.setFillColor(ACID)
c.setLineWidth(1.3)
c.line(cx, cy + 47 * mm, cx, cy + 54 * mm)
c.line(cx, cy + 54 * mm, cx - 2.3 * mm, cy + 50.5 * mm)
c.line(cx, cy + 54 * mm, cx + 2.3 * mm, cy + 50.5 * mm)
text(c, 24 * mm, 153 * mm, "REAR / THICK EDGE / USB SIDE (+Y)", 8.4, True)

text(c, 14 * mm, 29 * mm, "Ø94 PART OUTLINE", 7.6, True)
text(c, 14 * mm, 23 * mm, "G-65 GROOVE SHOWN FOR ALIGNMENT ONLY", 7.2)
text(c, 14 * mm, 17 * mm, "ALL REFERENCE GEOMETRY: DO NOT MARK", 7.2, True, RED)

rx = 130 * mm
text(c, rx, 153 * mm, "FACTORY INSTRUCTION", 11, True)
c.setStrokeColor(GRID)
c.line(rx, 149 * mm, W - 14 * mm, 149 * mm)
bullet(c, rx, 139 * mm, "Accept laser marking instead of machined/recessed text.")
bullet(c, rx, 129 * mm, "Laser after fine bead blast + black matte anodizing.")
bullet(c, rx, 119 * mm, "Result: natural aluminum / silver mark on black surface.")
bullet(c, rx, 109 * mm, "Hatch/fill LASER_MARK as compound glyphs; preserve counters/holes.")
bullet(c, rx, 99 * mm, "Do not resize, rotate, mirror, or substitute the font.")
bullet(c, rx, 89 * mm, "Do not machine the 0.25 mm-deep text contained in the STEP.")
bullet(c, rx, 79 * mm, "Preserve the O-ring groove, holes, wedge angle, and all other geometry.")

c.setFillColor(colors.white)
c.setStrokeColor(GRID)
c.roundRect(rx, 31 * mm, W - rx - 14 * mm, 37 * mm, 2 * mm, fill=1, stroke=1)
text(c, rx + 5 * mm, 59 * mm, "CONTROLLED ARTWORK", 9, True)
main, strap = GEOMETRY["artwork"]
text(c, rx + 5 * mm, 50 * mm, f"CODEX KEYBORED: {main['bounds']['maxX'] - main['bounds']['minX']:.3f} × {main['bounds']['maxY'] - main['bounds']['minY']:.3f} mm outlines; 4.2 mm nominal font size", 8)
text(c, rx + 5 * mm, 43 * mm, f"ABSOLUTELY VIBE-CODED: {strap['bounds']['maxX'] - strap['bounds']['minX']:.3f} × {strap['bounds']['maxY'] - strap['bounds']['minY']:.3f} mm outlines; 2.1 mm nominal font size", 8)
text(c, rx + 5 * mm, 36 * mm, "Origin: part center (0,0). Main center Y +4.000; strapline Y -4.000.", 8)

c.setFillColor(RED)
c.roundRect(rx, 13 * mm, W - rx - 14 * mm, 12 * mm, 2 * mm, fill=1, stroke=0)
text(c, rx + 5 * mm, 17 * mm, "ONLY THE LASER_MARK LAYER IS PRODUCTION ARTWORK", 9.2, True, colors.white)

text(c, 14 * mm, 7 * mm, "PART: CM2-002_bottom_weight.step · ITEM: CNC2607185001881-3086316A", 7)
c.drawRightString(W - 14 * mm, 7 * mm, "FIRST ARTICLE · CONTACT CUSTOMER BEFORE ANY ARTWORK CHANGE")
c.save()
print(f"Generated {OUT}")
