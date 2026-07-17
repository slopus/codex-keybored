"""Export a Freerouting DSN without the high-fanout GND net.

The production board retains every electrical assignment. This temporary view
removes GND from pads and preserves all other valid routing so Freerouting can
finish implicated signal and supply rails without trying to create a 99-pad
point-to-point ground tree. Ground is restored by post-route pours.
"""

from pathlib import Path
from math import cos, pi, sin
import re
import os

import pcbnew


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"
TEMP_BOARD = ROOT / "kicad" / "codex_micro_wired_revA_route_signals.kicad_pcb"
OUTPUT_DSN = ROOT / "kicad" / "codex_micro_wired_revA_route_signals.dsn"
TRACKS_TO_REBUILD = {"GND"}
ROUTE_FROM_SCRATCH = os.environ.get("CODEX_ROUTE_FROM_SCRATCH") == "1"

board = pcbnew.LoadBoard(str(SOURCE))
cleared = 0
removed_tracks = 0
zones_to_remove = list(board.Zones())
tracks_to_scan = list(board.GetTracks())
for zone in zones_to_remove:
    board.Remove(zone)
for track in tracks_to_scan:
    if (ROUTE_FROM_SCRATCH and not track.IsLocked()) or track.GetNetname() in TRACKS_TO_REBUILD:
        board.Remove(track)
        removed_tracks += 1
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        if pad.GetNetname() == "GND":
            pad.SetNetCode(0)
            cleared += 1


def add_route_keepout(x, y, radius):
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


# Freerouting does not infer every footprint-local Edge.Cuts opening as a
# route obstacle. Explicit temporary keepouts protect the reverse-mount LED
# windows and every mechanical NPTH during the DSN round trip.
keepouts = []
for footprint in board.GetFootprints():
    if footprint.GetReference().startswith("LED"):
        position = footprint.GetPosition()
        keepouts.append((pcbnew.ToMM(position.x), pcbnew.ToMM(position.y), 1.90))
    for pad in footprint.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            position = pad.GetPosition()
            radius = pcbnew.ToMM(pad.GetDrillSize().x) / 2 + 0.30
            keepouts.append((pcbnew.ToMM(position.x), pcbnew.ToMM(position.y), radius))
for x, y, radius in keepouts:
    add_route_keepout(x, y, radius)

pcbnew.SaveBoard(str(TEMP_BOARD), board)
if not pcbnew.ExportSpecctraDSN(board, str(OUTPUT_DSN)):
    raise SystemExit("Specctra DSN export failed")

# KiCad exports every copper layer as a signal layer.  Mark the dedicated
# planes explicitly so Freerouting does not spend routing capacity on them.
# GND alone is deliberately absent here. In4 remains a routable signal layer;
# +5 V, +3V3 and +1V1 are completed as ordinary nets before optional pours.
dsn = OUTPUT_DSN.read_text()
dsn = dsn.replace(
    "(layer GND_PLANE\n      (type signal)",
    "(layer GND_PLANE\n      (type power)",
)
# The RP2040 fanout is dense but still inside JLCPCB's standard multilayer
# capability.  Use 0.15 mm traces and 0.45/0.20 mm through-vias for the
# autorouter round trip; this avoids HDI/blind vias while leaving adequate
# annular ring and 0.15 mm copper clearance.
dsn = dsn.replace("Via[0-5]_600:300_um", "Via[0-5]_450:200_um")
via_block_pattern = re.compile(
    r'(\(padstack "Via\[0-5\]_450:200_um".*?\n\s*\(attach off\)\n\s*\))',
    re.DOTALL,
)
via_match = via_block_pattern.search(dsn)
if not via_match:
    raise SystemExit("Could not locate the exported through-via padstack")
via_block = via_match.group(1).replace(") 600)", ") 450)")
dsn = dsn[:via_match.start()] + via_block + dsn[via_match.end():]
dsn = dsn.replace("(width 200)", "(width 150)")
OUTPUT_DSN.write_text(dsn)

print(
    f"Exported {OUTPUT_DSN.name}; omitted {cleared} GND pads and removed "
    f"{removed_tracks} GND tracks/vias; added {len(keepouts)} "
    "temporary route keepouts; marked In1 as GND plane; "
    + ("routed from scratch" if ROUTE_FROM_SCRATCH else "preserved existing signal routes")
)
