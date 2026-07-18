"""Generate the revision-B CNC drawing pack from controlled dimensions."""

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
        "name": "GLOSS BLACK UPPER HOUSING",
        "step": "CM2-001_upper_housing.step",
        "render": "revb-cm2-001-upper.png",
        "material": "POM (black), CNC machined",
        "finish": "No bead blast. Strict cosmetic A-surfaces; smooth/semi-gloss, target Ra ≤ 0.8 µm.",
        "critical": [
            ("Overall", "108.00 × 108.00 × 10.30 mm"),
            ("Inner opening", "92.00 × 92.00 mm, R7.00 mm"),
            ("PCB mounting", "4× M3×0.5, pitch 78.00 × 78.00 mm; 6.0 min full thread"),
            ("Base mounting", "4× M2.5×0.45 at cardinal R41.00; 5.0 min full thread"),
            ("Light-guide pocket", "106.40 outer, 1.50 deep; floor Z8.80"),
            ("Rear USB-C notch", "11.00 × 4.60 mm capsule; center Z9.80, open top"),
        ],
        "notes": [
            "Break exposed edges 0.20–0.40 mm; do not round locating faces.",
            "Tap threads directly in POM; thread axes are normal to PCB/top datum.",
            "Protect all exterior faces from clamp marks and shipping scratches.",
            "Rear Ø4.20 service hole is reserved for a future Bluetooth PCB actuator.",
        ],
        "diagram": "upper",
    },
    {
        "id": "CM2-002",
        "name": "ANGLED BOTTOM WEIGHT",
        "step": "CM2-002_bottom_weight.step",
        "render": "revb-cm2-002-bottom.png",
        "material": "6061-T6 aluminum",
        "finish": "Fine bead blast + matte black anodize",
        "critical": [
            ("Plan diameter", "Ø94.00 mm"),
            ("Front thickness", "3.80 mm nominal"),
            ("Rear thickness", "12.00 mm nominal"),
            ("Underside angle", "5.0° nominal; top datum remains planar"),
            ("Mounting holes", "4× Ø2.80 THRU at cardinal R41.00"),
            ("Counterbores", "4× Ø5.00 × 1.90 deep from local angled underside"),
            ("G-65 O-ring groove", "Ø67.50 centerline × 3.60 wide × 2.20 deep; normal to underside"),
            ("Logo", "Engrave 0.25 deep after anodize; geometry included in STEP"),
        ],
        "notes": [
            "Engraving reads CODEX KEYBORED / ABSOLUTELY VIBE-CODED in bare silver.",
            "Protect planar top datum; deburr 0.20–0.40 mm.",
        ],
        "diagram": "wedge",
    },
    {
        "id": "CM2-003",
        "name": "MANDATORY CAPTURED LIGHT GUIDE",
        "step": "CM2-003_lightpipe.step",
        "render": "revb-cm2-003-lightpipe.png",
        "material": "Clear cast PMMA",
        "finish": "Transparent-polished edges; uniform fine frost on top optical face.",
        "critical": [
            ("Outer", "106.10 × 106.10 mm, R13.05"),
            ("Inner opening", "91.20 × 91.20 mm, R6.60"),
            ("Thickness", "1.50 mm; flatness ≤ 0.20 mm"),
            ("Rear opening", "12.00 mm wide USB relief"),
            ("Pocket fit", "0.15 mm nominal clearance per side"),
        ],
        "notes": [
            "This part is mandatory with the opaque black housing.",
            "No opaque contamination; frost only the indicated optical face.",
            "Protect both faces with removable film for shipping.",
        ],
        "diagram": "lightpipe",
    },
    {
        "id": "CM2-004",
        "name": "JOYSTICK CAP FIT PROTOTYPE",
        "step": "CM2-004_joystick_cap.step",
        "render": "revb-cm2-004-cap.png",
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
    {
        "id": "CM2-005",
        "name": "PURCHASED CONTINUOUS ANTI-SLIP RING",
        "step": "vendor_reference/JLCMC_AMFG-P5-A65-65_G65_oring.step",
        "render": "revb-jlcmc-g65-oring.png",
        "material": "Black nitrile rubber (NBR), 65 Shore A",
        "finish": "As supplied; captured mechanically, no adhesive.",
        "critical": [
            ("Supplier / P/N", "JLCMC AMFG-P5-A65-65; JIS B 2401 G-65; use 1"),
            ("Inner diameter", "Ø64.40 ±0.57 mm"),
            ("Cross section", "Ø3.10 ±0.10 mm; nominal OD Ø70.60 mm"),
            ("Retention groove", "Ø67.50 centerline × 3.60 wide × 2.20 deep"),
            ("Installed protrusion", "0.90 mm nominal; groove-to-counterbore land 2.95 mm"),
            ("Live price", "$0.1522 each, in stock on 2026-07-17"),
            ("Base screw set", "1× M2.5×8, 2× M2.5×12, 1× M2.5×16; ISO 10642"),
        ],
        "notes": [
            "This one continuous ring replaces both the rejected TPU part and discrete feet.",
            "Install after anodizing: clean and dry the groove, seat evenly, and remove all twist.",
            "No glue, printing, trimming, or rubber fabrication is required.",
            "Purchase: jlcmc.com/product/s/A05/AMFG/o-ring-g-series",
        ],
        "diagram": "oring",
    },
]


def header(c, part, page_number, page_total):
    c.setFillColor(INK)
    c.rect(0, H - 25 * mm, W, 25 * mm, fill=1, stroke=0)
    c.setFillColor(ACID)
    c.setFont(FONT_BOLD, 9)
    c.drawString(14 * mm, H - 9 * mm, "CODEX KEYBORED / CNC DRAWING PACK")
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 18)
    c.drawString(14 * mm, H - 19 * mm, f"{part['id']}  {part['name']}")
    c.setFont(FONT, 8)
    c.drawRightString(W - 14 * mm, H - 10 * mm, "REV B · 2026-07-17 · mm")
    c.drawRightString(W - 14 * mm, H - 18 * mm, f"SHEET {page_number}/{page_total} · NOT TO SCALE")


def footer(c, part):
    y = 10 * mm
    c.setStrokeColor(GRID)
    c.line(14 * mm, y + 7 * mm, W - 14 * mm, y + 7 * mm)
    c.setFillColor(INK)
    c.setFont(FONT, 6.8)
    c.drawString(14 * mm, y, f"MASTER MODEL: {part['step']}")
    c.drawRightString(W - 14 * mm, y, "REV B · UNITS mm · STEP CONTROLS UNLISTED GEOMETRY")
    c.drawString(14 * mm, y - 4.5 * mm, "DEFAULT UNLESS NOTED: ISO 2768-m · DEBURR · FIRST ARTICLE INSPECTION REQUIRED")
    c.drawRightString(W - 14 * mm, y - 4.5 * mm, "PRIVATE PROTOTYPE / NOT AN OFFICIAL WORK LOUDER DRAWING")


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
        inset = side * (8 if kind == "upper" else 7.45) / 108
        c.roundRect(left + inset, bottom + inset, side - 2 * inset, side - 2 * inset, 5 * mm, fill=0, stroke=1)
        if kind == "lightpipe":
            c.setFillColor(PALE); c.setStrokeColor(PALE)
            c.rect(x + w / 2 - 6 * mm, bottom + side - 2 * mm, 12 * mm, 8 * mm, fill=1, stroke=0)
            c.setStrokeColor(INK); c.setFillColor(INK)
        c.setFont(FONT_BOLD, 8); c.drawCentredString(x + w / 2, y + h / 2, "92.00 OPENING" if kind == "upper" else "91.20 OPENING")
        outer_label = "108.00" if kind == "upper" else "106.10"
        radius_label = "R14.00" if kind == "upper" else "R13.05"
        arrow(c, left, bottom - 8 * mm, left + side, bottom - 8 * mm, outer_label)
        c.setFont(FONT_BOLD, 8); c.drawString(left + 2 * mm, bottom + side + 5 * mm, radius_label)
    elif kind == "oring":
        cx, cy = x + w / 2, y + h / 2
        scale = min(w, h) * .010
        ro = 35.3 * scale
        ri = 32.2 * scale
        c.circle(cx - 18 * mm, cy + 2 * mm, ro, fill=0, stroke=1)
        c.circle(cx - 18 * mm, cy + 2 * mm, ri, fill=0, stroke=1)
        arrow(c, cx - 18 * mm - ro, cy - ro - 7 * mm, cx - 18 * mm + ro, cy - ro - 7 * mm, "Ø70.60")
        section_x = cx + 36 * mm
        c.circle(section_x, cy + 2 * mm, 6 * mm, fill=0, stroke=1)
        arrow(c, section_x - 6 * mm, cy - 12 * mm, section_x + 6 * mm, cy - 12 * mm, "Ø3.10")
        c.setFont(FONT_BOLD, 8); c.drawCentredString(cx, y + 5 * mm, "JLCMC AMFG-P5-A65-65 · JIS G-65 · 1 PC")
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
    table_height = (8 + 9 * len(part["critical"])) * mm
    table = Table(rows, colWidths=[45 * mm, tw - 45 * mm], rowHeights=[8 * mm] + [9 * mm] * len(part["critical"]))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .4, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    table.wrapOn(c, tw, table_height); table.drawOn(c, tx, content_top - table_height)

    section_top = content_top - table_height - 8 * mm
    c.setFillColor(INK); c.setFont(FONT_BOLD, 9); c.drawString(tx, section_top, "MATERIAL")
    c.setFont(FONT, 8); c.drawString(tx, section_top - 6 * mm, part["material"])
    c.setFont(FONT_BOLD, 9); c.drawString(tx, section_top - 16 * mm, "FINISH")
    c.setFont(FONT, 8); c.drawString(tx, section_top - 22 * mm, part["finish"])
    c.setFont(FONT_BOLD, 9); c.drawString(tx, section_top - 33 * mm, "MANUFACTURING NOTES")
    c.setFont(FONT, 8)
    y = section_top - 40 * mm
    for note in part["notes"]:
        c.drawString(tx, y, f"•  {note}")
        y -= 5 * mm
    c.setFillColor(colors.HexColor("#7e321e") if part["id"] == "CM2-002" else colors.HexColor("#20320f"))
    c.roundRect(tx, 23 * mm, tw, 18 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD, 9)
    if part["id"] == "CM2-005":
        acceptance = "ACCEPTANCE: VERIFY SUPPLIER PART NUMBER AND GROOVE FIT"
        acceptance_note = "Vendor STEP is a fit reference only; purchase the exact JLCMC part listed above."
    else:
        acceptance = "ACCEPTANCE: VERIFY CRITICAL DIMENSIONS ON FIRST ARTICLE"
        acceptance_note = "Manufacture to STEP for all unlisted geometry; do not infer hidden threads or fits."
    c.drawString(tx + 5 * mm, 34 * mm, acceptance)
    c.setFont(FONT, 7.5); c.drawString(tx + 5 * mm, 27 * mm, acceptance_note)
    c.showPage()


def generate(filename, parts):
    canvas = Canvas(str(OUT / filename), pagesize=PAGE, pageCompression=1)
    for index, part in enumerate(parts, 1):
        draw_page(canvas, part, index, len(parts))
    canvas.save()


OUT.mkdir(parents=True, exist_ok=True)
generate("CM2_CNC_Drawing_Pack_RevB.pdf", PARTS)
for index, part in enumerate(PARTS, 1):
    generate(f"{part['id']}_Drawing_RevB.pdf", [part])
print("Generated Rev B drawing/procurement pack and five per-part PDFs")
