"""Add production GND/+5 V pours and GND stitching vias after SES import."""

from math import cos, pi, sin
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"


def mm(value):
    return pcbnew.FromMM(value)


def point(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def rounded_outline(inset=0.55, radius=4.0, samples=8):
    points = []
    corners = [
        (90 - radius, radius, -pi / 2, 0),
        (90 - radius, 90 - radius, 0, pi / 2),
        (radius, 90 - radius, pi / 2, pi),
        (radius, radius, pi, 3 * pi / 2),
    ]
    effective_radius = radius - inset
    for cx, cy, start, end in corners:
        for index in range(samples + 1):
            angle = start + (end - start) * index / samples
            points.append(
                point(cx + effective_radius * cos(angle), cy + effective_radius * sin(angle))
            )
    return points


board = pcbnew.LoadBoard(str(BOARD_PATH))
gnd = board.FindNet("GND")
plus5 = board.FindNet("+5V")
if gnd is None or plus5 is None:
    raise SystemExit("GND or +5V net is missing")

# Idempotent rebuild: remove only zones/vias carrying our explicit marker net
# and recognize generated zones by their three production layers.
generated = {
    ("GND", pcbnew.F_Cu), ("GND", pcbnew.In1_Cu), ("GND", pcbnew.B_Cu),
    ("+5V", pcbnew.In4_Cu),
}
zones_to_remove = list(board.Zones())
tracks_to_scan = list(board.GetTracks())
for zone in zones_to_remove:
    if (zone.GetNetname(), zone.GetLayer()) in generated or zone.GetZoneName() == "TOUCH_NO_POUR":
        board.Remove(zone)

# Remove a previous run's generated stitching vias before rebuilding them.
# This keeps the post-process safe to repeat while preserving router-created
# vias everywhere else on the board.
stitch_positions = [
    (25, 5), (65, 5), (25, 85), (65, 85),
    (5, 25), (85, 25), (5, 58), (85, 58),
]
stitch_set = {(mm(x), mm(y)) for x, y in stitch_positions}
for track in tracks_to_scan:
    if (
        isinstance(track, pcbnew.PCB_VIA)
        and track.GetNetname() == "GND"
        and (track.GetPosition().x, track.GetPosition().y) in stitch_set
        and track.GetWidth() == mm(0.65)
        and track.GetDrillValue() == mm(0.30)
    ):
        board.Remove(track)

def set_single_layer(zone, layer):
    layers = pcbnew.LSET()
    layers.AddLayer(layer)
    zone.SetLayerSet(layers)


outline_points = rounded_outline()
for plane_net, layer in (
    (gnd, pcbnew.F_Cu), (gnd, pcbnew.In1_Cu), (gnd, pcbnew.B_Cu),
    (plus5, pcbnew.In4_Cu),
):
    zone = pcbnew.ZONE(board)
    set_single_layer(zone, layer)
    zone.SetNet(plane_net)
    zone.SetLocalClearance(mm(0.20))
    zone.SetMinThickness(mm(0.18))
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zone.SetPadConnection(
        pcbnew.ZONE_CONNECTION_FULL
        if plane_net.GetNetname() == "GND"
        else pcbnew.ZONE_CONNECTION_THERMAL
    )
    polygon = zone.Outline()
    polygon.NewOutline()
    for vertex in outline_points:
        polygon.Append(vertex)
    board.Add(zone)

# A copper-plane void under the 14 mm capacitive electrode is required for
# usable sensitivity. Tracks/vias remain permitted so the electrode itself can
# escape to U6; every zone fill on all six copper layers is prohibited here.
touch_keepout = pcbnew.ZONE(board)
touch_keepout.SetZoneName("TOUCH_NO_POUR")
touch_keepout.SetIsRuleArea(True)
touch_keepout.SetDoNotAllowZoneFills(True)
touch_keepout.SetDoNotAllowTracks(False)
touch_keepout.SetDoNotAllowVias(False)
touch_keepout.SetDoNotAllowPads(False)
touch_keepout.SetDoNotAllowFootprints(False)
touch_layers = pcbnew.LSET()
for layer in (
    pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
    pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu,
):
    touch_layers.AddLayer(layer)
touch_keepout.SetLayerSet(touch_layers)
touch_outline = touch_keepout.Outline()
touch_outline.NewOutline()
for index in range(48):
    angle = 2 * pi * index / 48
    touch_outline.Append(point(16.425 + 8.2 * cos(angle), 73.575 + 8.2 * sin(angle)))
board.Add(touch_keepout)

# Eight deliberately peripheral through-vias join the top/bottom pours to the
# dedicated In1 ground plane without placing drill holes inside SMD lands.
for x, y in stitch_positions:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(point(x, y))
    via.SetWidth(mm(0.65))
    via.SetDrill(mm(0.30))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(gnd)
    board.Add(via)

pcbnew.SaveBoard(str(BOARD_PATH), board)
print(
    f"Added GND pours, +5V plane, touch no-pour area, and "
    f"{len(stitch_positions)} GND stitching vias"
)
