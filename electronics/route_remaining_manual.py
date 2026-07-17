"""Hand-route the dense controller island before the board-wide pass.

The RP2040 power/flash routes use short, explicit inner-layer corridors.  SWD
uses a service corridor between key columns and terminates at its bottom-side
test pad.  Every item is locked so a repeat import cannot remove the reviewed
geometry.
"""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"


def mm(value):
    return pcbnew.FromMM(value)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_track(board, net_code, layer, start, end, width=0.15):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start)
    track.SetEnd(end)
    track.SetLayer(layer)
    track.SetWidth(mm(width))
    # Use the numeric code, not a temporary SWIG NETINFO_ITEM proxy.  Keeping
    # several FindNet() proxies in a Python dictionary can leave new copper
    # attached to a later, unrelated net after the board is saved.
    track.SetNetCode(net_code)
    track.SetLocked(True)
    board.Add(track)


def add_path(board, net_code, layer, points):
    for start, end in zip(points, points[1:]):
        add_track(board, net_code, layer, vec(*start), vec(*end))


def add_via(board, net_code, point):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(vec(*point))
    via.SetWidth(mm(0.45))
    via.SetDrill(mm(0.20))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNetCode(net_code)
    via.SetLocked(True)
    board.Add(via)


board = pcbnew.LoadBoard(str(BOARD_PATH))
route_nets = {
    "+1V1", "QSPI_SD2", "QSPI_SD3", "SWD", "USB_DP_CONN",
}

# Make repeated runs deterministic without touching imported routes.
for item in list(board.GetTracks()):
    if item.IsLocked() and item.GetNetname() in route_nets:
        board.Remove(item)

net = {name: board.FindNet(name).GetNetCode() for name in route_nets}
if any(value <= 0 for value in net.values()):
    raise RuntimeError("One or more manual-route nets are missing")

# QSPI_SD3: U1.51 -> U2.7, around the left side of the flash.
sd3_start = (45.6000, 23.5625)
sd3_top_via = (45.6000, 21.5000)
sd3_flash_via = (40.1000, 35.3650)
add_path(board, net["QSPI_SD3"], pcbnew.B_Cu, [sd3_start, sd3_top_via])
add_via(board, net["QSPI_SD3"], sd3_top_via)
add_path(
    board,
    net["QSPI_SD3"],
    pcbnew.In3_Cu,
    [sd3_top_via, (45.6000, 20.5000), (38.5000, 20.5000),
     (38.5000, 35.3650), sd3_flash_via],
)
add_via(board, net["QSPI_SD3"], sd3_flash_via)
add_path(
    board,
    net["QSPI_SD3"],
    pcbnew.B_Cu,
    [sd3_flash_via, (41.4125, 35.3650)],
)

# QSPI_SD2: U1.52 -> U2.3, mirrored around the right side of the flash.
sd2_start = (46.0000, 23.5625)
sd2_top_via = (46.8000, 21.2000)
sd2_flash_via = (49.8500, 36.6350)
add_path(
    board,
    net["QSPI_SD2"],
    pcbnew.B_Cu,
    [sd2_start, (46.0000, 22.8000), (46.8000, 22.0000), sd2_top_via],
)
add_via(board, net["QSPI_SD2"], sd2_top_via)
add_path(
    board,
    net["QSPI_SD2"],
    pcbnew.In2_Cu,
    [sd2_top_via, (50.7500, 21.2000), (50.7500, 36.6350), sd2_flash_via],
)
add_via(board, net["QSPI_SD2"], sd2_flash_via)
add_path(
    board,
    net["QSPI_SD2"],
    pcbnew.B_Cu,
    [sd2_flash_via, (48.5875, 36.6350)],
)

# RP2040 internal rail: U1.23 -> U1.34.  Both vias sit outside the QFN and
# clear the bottom-side C6 pads; the other +1V1 pins remain for the board-wide
# router to connect to the same local island.
v11_start = (44.4000, 30.4375)
v11_via = (45.2000, 31.9000)
v11_anchor_via = (41.0000, 27.6000)
v11_anchor_pad = (41.5625, 27.6000)
add_path(
    board,
    net["+1V1"],
    pcbnew.B_Cu,
    [v11_start, (44.4000, 31.1000), v11_via],
)
add_via(board, net["+1V1"], v11_via)
add_path(
    board,
    net["+1V1"],
    pcbnew.In2_Cu,
    [v11_via, (44.1000, 33.0000), (41.0000, 33.0000), v11_anchor_via],
)
add_via(board, net["+1V1"], v11_anchor_via)
add_path(
    board,
    net["+1V1"],
    pcbnew.B_Cu,
    [v11_anchor_via, v11_anchor_pad],
)

# Join the two remaining top-edge +1V1 pins to the same local rail island.
v11_top_left_pad = (43.6000, 23.5625)
v11_top_right_pad = (45.2000, 23.5625)
v11_top_left_via = (43.6000, 21.3000)
v11_top_right_via = (44.8000, 21.3000)
add_path(board, net["+1V1"], pcbnew.B_Cu, [v11_top_left_pad, v11_top_left_via])
add_via(board, net["+1V1"], v11_top_left_via)
add_path(
    board,
    net["+1V1"],
    pcbnew.B_Cu,
    [v11_top_right_pad, (45.2000, 22.8000),
     (44.8000, 22.4000), v11_top_right_via],
)
add_via(board, net["+1V1"], v11_top_right_via)
add_path(
    board,
    net["+1V1"],
    pcbnew.In2_Cu,
    [v11_top_right_via, v11_top_left_via, (41.5000, 21.3000),
     (41.5000, 26.5000), v11_anchor_via],
)

# Debug data: U1.25 -> TP2.  The inner-layer dogleg stays between switch
# through-holes; the last leg is on B.Cu because TP2 is a bottom-only pad.
swd_start = (43.6000, 30.4375)
swd_core_via = (43.0000, 31.6000)
swd_tp_via = (68.0000, 85.5000)
add_path(
    board,
    net["SWD"],
    pcbnew.B_Cu,
    [swd_start, (43.6000, 31.0000), swd_core_via],
)
add_via(board, net["SWD"], swd_core_via)
add_path(
    board,
    net["SWD"],
    pcbnew.In4_Cu,
    [swd_core_via, (40.0000, 31.6000), (40.0000, 28.5000),
     (25.0000, 28.5000), (25.0000, 81.5000), (42.8000, 81.5000),
     (42.8000, 84.0000), (47.2000, 84.0000), (47.2000, 81.5000),
     (68.0000, 81.5000), swd_tp_via],
)
add_via(board, net["SWD"], swd_tp_via)
add_path(board, net["SWD"], pcbnew.B_Cu, [swd_tp_via, (68.0000, 87.0000)])

# USB-C A6/B6 are the same D+ net.  Join them behind the connector contacts,
# clear of the intervening D- pads.
add_path(
    board,
    net["USB_DP_CONN"],
    pcbnew.F_Cu,
    [(44.7500, 1.0550), (44.7500, 2.2000),
     (45.7500, 2.2000), (45.7500, 1.0550)],
)

board.SynchronizeNetsAndNetClasses(False)
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(
    "Locked controller routes: +1V1, QSPI_SD2, QSPI_SD3, SWD, USB_DP_CONN"
)
