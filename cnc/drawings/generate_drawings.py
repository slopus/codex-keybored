"""Generate the revision-A CNC drawing pack from controlled dimensions."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RENDERS = ROOT / "docs" / "assets" / "renders"
PAGE = landscape(A4)
W, H = PAGE

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
for candidate in (
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
):
    if candidate.exists():
        pdfmetrics.registerFont(TTFont("DrawingSans", str(candidate)))
        FONT = "DrawingSans"
        break

INK = colors.HexColor("#11130f")
ACID = colors.HexColor("#a7d528")
GRID = colors.HexColor("#cfd2c9")
PALE = colors.HexColor("#f4f5f1")


PARTS = [
    {
        "id": "CM2-001",
        "name": "UPPER HOUSING",
        "step": "CM2-001_upper_housing.step",
        "render": "fusion-cm2-001-upper-housing.png",
        "material": "Cast polycarbonate; alternate cast PMMA or stabilized hardwood",
        "finish": "Uniform diffuse matte. No transparent polish required.",
        "critical": [
            ("Overall", "108.00 × 108.00 × 10.30 mm"),
            ("Outer corners", "R14.00 mm"),
            ("Inner opening", "92.00 × 92.00 mm, R7.00 mm"),
            ("PCB clearance", "0.20–0.30 mm total, validate first article"),
        ],
        "notes": [
            "Break exposed edges 0.20–0.40 mm; no sharp edges.",
            "Do not cut structural threads directly in PMMA.",
            "Protect cosmetic A-surfaces after bead/frost finish.",
        ],
        "diagram": "upper",
    },
    {
        "id": "CM2-002",
        "name": "ANGLED BOTTOM WEIGHT",
        "step": "CM2-002_bottom_weight.step",
        "render": "fusion-cm2-002-bottom-weight-side.png",
        "material": "6061-T6 aluminum",
        "finish": "Fine bead blast + matte black anodize",
        "critical": [
            ("Plan diameter", "Ø94.00 mm"),
            ("Front thickness", "3.80 mm nominal"),
            ("Rear thickness", "12.00 mm nominal"),
            ("Underside angle", "5.0° nominal; top datum remains planar"),
        ],
        "notes": [
            "This REPLACES the obsolete flat-bottom quote.",
            "Protect planar top datum; deburr 0.20–0.40 mm.",
            "No threads in Rev A solid: machine only after fit-check approval.",
        ],
        "diagram": "wedge",
    },
    {
        "id": "CM2-003",
        "name": "OPTIONAL LIGHT PIPE",
        "step": "CM2-003_optional_lightpipe.step",
        "render": "fusion-cm2-003-lightpipe.png",
        "material": "Cast PMMA, natural/frosted",
        "finish": "Uniform fine matte on light-emitting faces",
        "critical": [
            ("Overall", "108.00 × 108.00 × 1.50 mm"),
            ("Registration", "Match STEP; maintain flatness"),
            ("Optical edge", "No deep tool marks or opaque contamination"),
            ("Use", "Required with opaque or wood upper housing"),
        ],
        "notes": [
            "Do not flame-polish; target diffuse rather than clear transmission.",
            "Protect both faces with removable film for shipping.",
        ],
        "diagram": "lightpipe",
    },
    {
        "id": "CM2-004",
        "name": "JOYSTICK CAP FIT PROTOTYPE",
        "step": "CM2-004_joystick_cap.step",
        "render": "fusion-cm2-004-joystick-cap.png",
        "material": "Black POM for fit prototype only",
        "finish": "As-machined fine matte; deburr carefully",
        "critical": [
            ("Outside diameter", "Ø14.50 mm"),
            ("Overall height", "7.00 mm"),
            ("Shaft interface", "Per STEP; verify against selected joystick"),
            ("Final production", "Silicone Shore A 40–50 after fit validation"),
        ],
        "notes": [
            "Do not force onto a discontinued Alps sample.",
            "Machine one only and treat bore dimensions as provisional.",
        ],
        "diagram": "cap",
    },
]


def header(c, part, page_number, page_total):
    c.setFillColor(INK)
    c.rect(0, H - 25 * mm, W, 25 * mm, fill=1, stroke=0)
    c.setFillColor(ACID)
    c.setFont(FONT_BOLD, 9)
    c.drawString(14 * mm, H - 9 * mm, "CODEX MICRO / CNC DRAWING PACK")
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 18)
    c.drawString(14 * mm, H - 19 * mm, f"{part['id']}  {part['name']}")
    c.setFont(FONT, 8)
    c.drawRightString(W - 14 * mm, H - 10 * mm, "REV A · 2026-07-17 · mm")
    c.drawRightString(W - 14 * mm, H - 18 * mm, f"SHEET {page_number}/{page_total} · NOT TO SCALE")


def footer(c, part):
    y = 11 * mm
    c.setStrokeColor(GRID)
    c.line(14 * mm, y + 6 * mm, W - 14 * mm, y + 6 * mm)
    c.setFillColor(INK)
    c.setFont(FONT, 7.5)
    c.drawString(14 * mm, y, f"MASTER MODEL: {part['step']}")
    c.drawCentredString(W / 2, y, "DEFAULT UNLESS NOTED: ISO 2768-m · DEBURR · FIRST ARTICLE INSPECTION REQUIRED")
    c.drawRightString(W - 14 * mm, y, "PRIVATE PROTOTYPE / NOT AN OFFICIAL WORK LOUDER DRAWING")


def arrow(c, x1, y1, x2, y2, label):
    c.setStrokeColor(INK)
    c.setFillColor(INK)
    c.setLineWidth(0.7)
    c.line(x1, y1, x2, y2)
    for x, y, angle in ((x1, y1, 0), (x2, y2, 3.14159)):
        dx, dy = x2 - x1, y2 - y1
        length = max((dx * dx + dy * dy) ** 0.5, 1)
        ux, uy = dx / length, dy / length
        if angle:
            ux, uy = -ux, -uy
        c.line(x, y, x + (-ux + uy * .45) * 3 * mm, y + (-uy - ux * .45) * 3 * mm)
        c.line(x, y, x + (-ux - uy * .45) * 3 * mm, y + (-uy + ux * .45) * 3 * mm)
    c.setFont(FONT_BOLD, 9)
    c.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 2 * mm, label)


def technical_diagram(c, part, x, y, w, h):
    c.setFillColor(PALE)
    c.setStrokeColor(GRID)
    c.roundRect(x, y, w, h, 3 * mm, fill=1, stroke=1)
    c.setStrokeColor(INK)
    c.setFillColor(INK)
    kind = part["diagram"]
    if kind == "wedge":
        left, bottom = x + 18 * mm, y + 23 * mm
        width, front, rear = w - 36 * mm, 15 * mm, 42 * mm
        path = c.beginPath()
        path.moveTo(left, bottom)
        path.lineTo(left + width, bottom)
        path.lineTo(left + width, bottom + rear)
        path.lineTo(left, bottom + front)
        path.close()
        c.setFillColor(colors.HexColor("#d8dad4")); c.drawPath(path, fill=1, stroke=1)
        arrow(c, left, bottom - 9 * mm, left + width, bottom - 9 * mm, "Ø94.00")
        arrow(c, left - 8 * mm, bottom, left - 8 * mm, bottom + front, "3.80")
        arrow(c, left + width + 8 * mm, bottom, left + width + 8 * mm, bottom + rear, "12.00")
        c.setFont(FONT_BOLD, 9); c.drawString(left + width * .45, bottom + rear + 8 * mm, "PLANAR TOP DATUM A")
        c.drawString(left + width * .42, bottom + 12 * mm, "5.0°")
    elif kind in ("upper", "lightpipe"):
        side = min(w, h) - 8 * mm
        left, bottom = x + (w - side) / 2, y + (h - side) / 2
        c.setLineWidth(1.1); c.roundRect(left, bottom, side, side, 11 * mm, fill=0, stroke=1)
        if kind == "upper":
            inset = side * 8 / 108
            c.roundRect(left + inset, bottom + inset, side - 2 * inset, side - 2 * inset, 5 * mm, fill=0, stroke=1)
            c.setFont(FONT_BOLD, 8); c.drawCentredString(x + w / 2, y + h / 2, "92.00 OPENING")
        arrow(c, left, bottom - 8 * mm, left + side, bottom - 8 * mm, "108.00")
        c.setFont(FONT_BOLD, 8); c.drawString(left + 2 * mm, bottom + side + 5 * mm, "R14.00")
    else:
        cx, cy = x + w / 2, y + h / 2
        r = min(w, h) * 0.27
        c.circle(cx, cy, r, fill=0, stroke=1)
        arrow(c, cx - r, cy - r - 9 * mm, cx + r, cy - r - 9 * mm, "Ø14.50")
        c.setFont(FONT_BOLD, 8); c.drawCentredString(cx, cy, "HEIGHT 7.00")


def draw_page(c, part, page_number, page_total):
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header(c, part, page_number, page_total)
    footer(c, part)
    margin = 14 * mm
    content_top = H - 33 * mm
    left_w = 116 * mm
    render_path = RENDERS / part["render"]
    if render_path.exists():
        c.drawImage(str(render_path), margin, 70 * mm, left_w, 78 * mm, preserveAspectRatio=True, anchor="c", mask="auto")
    technical_diagram(c, part, margin, 23 * mm, left_w, 44 * mm)

    tx = margin + left_w + 10 * mm
    tw = W - tx - margin
    style = ParagraphStyle("drawing", fontName=FONT, fontSize=8, leading=11, textColor=INK)
    rows = [[Paragraph("<b>PROPERTY</b>", style), Paragraph("<b>CONTROLLED REQUIREMENT</b>", style)]]
    rows += [[Paragraph(k, style), Paragraph(v, style)] for k, v in part["critical"]]
    table = Table(rows, colWidths=[45 * mm, tw - 45 * mm], rowHeights=[9 * mm] + [13 * mm] * len(part["critical"]))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .4, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    table.wrapOn(c, tw, 80 * mm); table.drawOn(c, tx, content_top - 63 * mm)

    c.setFillColor(INK); c.setFont(FONT_BOLD, 9); c.drawString(tx, content_top - 73 * mm, "MATERIAL")
    c.setFont(FONT, 8); c.drawString(tx, content_top - 79 * mm, part["material"])
    c.setFont(FONT_BOLD, 9); c.drawString(tx, content_top - 89 * mm, "FINISH")
    c.setFont(FONT, 8); c.drawString(tx, content_top - 95 * mm, part["finish"])
    c.setFont(FONT_BOLD, 9); c.drawString(tx, content_top - 106 * mm, "MANUFACTURING NOTES")
    c.setFont(FONT, 8)
    y = content_top - 113 * mm
    for note in part["notes"]:
        c.drawString(tx, y, f"•  {note}")
        y -= 6 * mm
    c.setFillColor(colors.HexColor("#7e321e") if part["id"] == "CM2-002" else colors.HexColor("#20320f"))
    c.roundRect(tx, 23 * mm, tw, 18 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD, 9)
    c.drawString(tx + 5 * mm, 34 * mm, "ACCEPTANCE: VERIFY CRITICAL DIMENSIONS ON FIRST ARTICLE")
    c.setFont(FONT, 7.5); c.drawString(tx + 5 * mm, 27 * mm, "Manufacture to STEP for all unlisted geometry; do not infer hidden threads or fits.")
    c.showPage()


def generate(filename, parts):
    canvas = Canvas(str(OUT / filename), pagesize=PAGE, pageCompression=1)
    for index, part in enumerate(parts, 1):
        draw_page(canvas, part, index, len(parts))
    canvas.save()


OUT.mkdir(parents=True, exist_ok=True)
generate("CM2_CNC_Drawing_Pack_RevA.pdf", PARTS)
for index, part in enumerate(PARTS, 1):
    generate(f"{part['id']}_Drawing_RevA.pdf", [part])
print("Generated CNC drawing pack and four per-part PDFs")
