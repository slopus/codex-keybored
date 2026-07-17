"""Via-stitch every disconnected B.Cu GND-pour island to the In1 plane."""

from math import hypot
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"


def mm(value):
    return pcbnew.FromMM(value)


def to_mm(point):
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def point_segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return hypot(px - (ax + t * dx), py - (ay + t * dy))


def pole_of_outline(chain, step=0.10):
    vertices = [to_mm(chain.CPoint(i)) for i in range(chain.PointCount())]
    box = chain.BBox()
    x0, y0 = pcbnew.ToMM(box.GetX()), pcbnew.ToMM(box.GetY())
    x1 = x0 + pcbnew.ToMM(box.GetWidth())
    y1 = y0 + pcbnew.ToMM(box.GetHeight())
    best = None
    x = x0 + step / 2
    while x < x1:
        y = y0 + step / 2
        while y < y1:
            candidate = pcbnew.VECTOR2I(mm(x), mm(y))
            if chain.PointInside(candidate):
                clearance = min(
                    point_segment_distance(x, y, *vertices[i], *vertices[(i + 1) % len(vertices)])
                    for i in range(len(vertices))
                )
                if best is None or clearance > best[0]:
                    best = (clearance, x, y)
            y += step
        x += step
    return best


board = pcbnew.LoadBoard(str(BOARD_PATH))
gnd = board.FindNet("GND")
zone = next(
    z for z in board.Zones()
    if z.GetNetname() == "GND" and z.GetLayer() == pcbnew.B_Cu
)
if not zone.IsFilled():
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
polys = zone.GetFilledPolysList(pcbnew.B_Cu)

# Resolve every geometry-dependent value before mutating the SWIG board; KiCad
# invalidates borrowed polygon wrappers whenever a board item is removed.
outlines = [polys.COutline(i) for i in range(polys.OutlineCount())]
main_index = max(
    range(len(outlines)),
    key=lambda i: outlines[i].BBox().GetWidth() * outlines[i].BBox().GetHeight(),
)
islands = [
    (index, pole_of_outline(outline))
    for index, outline in enumerate(outlines)
    if index != main_index
]
pad35 = next(
    p for p in board.FindFootprintByReference("U1").Pads()
    if p.GetNumber() == "35"
)
pad35_xy = to_mm(pad35.GetPosition())

# Remove only a previous pass's small island vias and locked LQFP escape.
for item in list(board.GetTracks()):
    generated_via = (
        isinstance(item, pcbnew.PCB_VIA)
        and item.GetNetname() == "GND"
        and item.GetWidth(pcbnew.F_Cu) == mm(0.40)
        and item.GetDrillValue() == mm(0.20)
    )
    generated_escape = (
        isinstance(item, pcbnew.PCB_TRACK)
        and not isinstance(item, pcbnew.PCB_VIA)
        and item.GetNetname() == "GND"
        and item.IsLocked()
    )
    if generated_via or generated_escape:
        board.Remove(item)

added = []
for index, candidate in islands:
    if candidate is None:
        raise SystemExit(f"No point in GND island {index}")
    if candidate[0] < 0.20:
        # The only sub-via-width island is the narrow copper tongue attached
        # to U1 pad 35. Escape between the two nearby 0402 capacitors to an
        # ordinary through-via in the adjacent open ground region.
        if not (39.7 < candidate[1] < 42.2 and 24.5 < candidate[2] < 25.1):
            raise SystemExit(f"No 0.40 mm via site in GND island {index}: {candidate}")
        x, y = 39.90, 24.75
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(pcbnew.VECTOR2I(mm(pad35_xy[0]), mm(pad35_xy[1])))
        track.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
        track.SetLayer(pcbnew.B_Cu)
        track.SetWidth(mm(0.15))
        track.SetNet(gnd)
        track.SetLocked(True)
        board.Add(track)
        clearance = candidate[0]
    else:
        clearance, x, y = candidate
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    via.SetWidth(mm(0.40))
    via.SetDrill(mm(0.20))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(gnd)
    board.Add(via)
    added.append((index, round(x, 3), round(y, 3), round(clearance, 3)))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Added {len(added)} GND island vias: {added}")
