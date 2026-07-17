"""Hand-route the four reversible USB-C data pads without via-in-pad.

The HRO connector interleaves A6/A7/B6/B7, so the duplicated D+/D- contacts
must cross once.  Four 0.40/0.20 mm through-vias on the connector escape line
put D+ on SIGNAL_1 and D- on SIGNAL_2; each pair then travels to the USBLC6
on its own layer.  This is ordinary JLCPCB multilayer geometry, not HDI.
"""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"


def mm(value):
    return pcbnew.FromMM(value)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_track(board, net, layer, start, end, width=0.15):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(vec(*start))
    track.SetEnd(vec(*end))
    track.SetLayer(layer)
    track.SetWidth(mm(width))
    track.SetNet(net)
    track.SetLocked(True)
    board.Add(track)


def add_via(board, net, at):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(vec(*at))
    via.SetWidth(mm(0.40))
    via.SetDrill(mm(0.20))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(net)
    via.SetLocked(True)
    board.Add(via)


board = pcbnew.LoadBoard(str(BOARD_PATH))
nets = {name: board.FindNet(name) for name in ("USB_DP_CONN", "USB_DM_CONN")}

# Remove the autorouter's partial reversible-connector solution only.
for item in list(board.GetTracks()):
    if item.GetNetname() in nets:
        board.Remove(item)

# Straight 0.5 mm-pitch escapes; 0.40 mm vias leave the explicit 0.10 mm gap.
for name, x, via_y in (
    ("USB_DM_CONN", 44.25, 2.20),
    ("USB_DP_CONN", 44.75, 2.20),
    ("USB_DM_CONN", 45.25, 2.20),
    # B6 exits farther inward to clear the existing USB-CC2 fanout via.
    ("USB_DP_CONN", 45.75, 3.00),
):
    add_track(board, nets[name], pcbnew.F_Cu, (x, 1.055), (x, via_y))
    add_via(board, nets[name], (x, via_y))

# D+ crosses beneath D- on SIGNAL_1 and finishes beside USBLC6 pad 1.
for start, end in (
    ((44.75, 2.20), (44.75, 3.00)),
    ((44.75, 3.00), (45.75, 3.00)),
    ((44.75, 3.00), (47.00, 5.25)),
    ((47.00, 5.05), (47.00, 9.25)),
):
    add_track(board, nets["USB_DP_CONN"], pcbnew.In2_Cu, start, end)
add_via(board, nets["USB_DP_CONN"], (47.00, 9.25))
add_track(board, nets["USB_DP_CONN"], pcbnew.B_Cu, (47.00, 9.25), (46.138, 10.05))

# D- uses SIGNAL_2, so the two reversible pairs cross only in projection.
for start, end in (
    ((44.25, 2.20), (44.25, 3.30)),
    ((44.25, 3.30), (45.25, 3.30)),
    ((45.25, 3.30), (45.25, 2.20)),
    ((45.25, 3.30), (47.55, 5.60)),
    ((47.55, 5.60), (47.55, 11.10)),
):
    add_track(board, nets["USB_DM_CONN"], pcbnew.In3_Cu, start, end)
add_via(board, nets["USB_DM_CONN"], (47.55, 11.10))
add_track(board, nets["USB_DM_CONN"], pcbnew.B_Cu, (47.55, 11.10), (46.138, 11.95))

pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Routed reversible USB-C D+/D- fanout in {BOARD_PATH}")
