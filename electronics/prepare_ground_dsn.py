"""Export a focused Freerouting DSN that finishes only the GND network."""

from math import cos, pi, sin
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"
TEMP_BOARD = ROOT / "kicad" / "codex_micro_wired_revA_route_ground.kicad_pcb"
OUTPUT_DSN = ROOT / "kicad" / "codex_micro_wired_revA_route_ground.dsn"


def add_route_keepout(board, x, y, radius):
    zone = pcbnew.ZONE(board)
    zone.SetZoneName("TEMP_ROUTE_KEEPOUT")
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowFootprints(False)
    layers = pcbnew.LSET()
    for layer in (
        pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
        pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu,
    ):
        layers.AddLayer(layer)
    zone.SetLayerSet(layers)
    outline = zone.Outline()
    outline.NewOutline()
    for index in range(32):
        angle = 2 * pi * index / 32
        outline.Append(
            pcbnew.VECTOR2I(
                pcbnew.FromMM(x + radius * cos(angle)),
                pcbnew.FromMM(y + radius * sin(angle)),
            )
        )
    board.Add(zone)


board = pcbnew.LoadBoard(str(SOURCE))
zones = list(board.Zones())
tracks = list(board.GetTracks())
for zone in zones:
    board.Remove(zone)
removed = 0
for track in tracks:
    if track.GetNetname() == "GND":
        board.Remove(track)
        removed += 1

cleared = 0
keepouts = []
for footprint in board.GetFootprints():
    if footprint.GetReference().startswith("LED"):
        position = footprint.GetPosition()
        keepouts.append((pcbnew.ToMM(position.x), pcbnew.ToMM(position.y), 1.90))
    for pad in footprint.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            position = pad.GetPosition()
            keepouts.append((
                pcbnew.ToMM(position.x), pcbnew.ToMM(position.y),
                pcbnew.ToMM(pad.GetDrillSize().x) / 2 + 0.30,
            ))
        elif pad.GetNetname() != "GND":
            pad.SetNetCode(0)
            cleared += 1
for x, y, radius in keepouts:
    add_route_keepout(board, x, y, radius)

pcbnew.SaveBoard(str(TEMP_BOARD), board)
if not pcbnew.ExportSpecctraDSN(board, str(OUTPUT_DSN)):
    raise SystemExit("Specctra GND DSN export failed")
print(
    f"Exported {OUTPUT_DSN.name}; cleared {cleared} non-GND pads, removed "
    f"{removed} GND routes, preserved other tracks, added {len(keepouts)} keepouts"
)
