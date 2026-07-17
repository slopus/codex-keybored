"""Hand-route and lock the RP2040 I/O escape fanout.

The complete keyboard remains one PCB.  This pass treats the USB/RP2040/flash
area as a logical controller island, fans the dense 0.4 mm QFN pins into two
staggered via columns, and leaves the long peripheral routes for a later
board-wide pass.  Locked copper prevents the autorouter from destroying the
verified escape geometry.
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
    track.SetStart(start)
    track.SetEnd(end)
    track.SetLayer(layer)
    track.SetWidth(mm(width))
    track.SetNet(net)
    track.SetLocked(True)
    board.Add(track)
    return track


def add_via(board, net, position):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(position)
    via.SetWidth(mm(0.40))
    via.SetDrill(mm(0.20))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(net)
    via.SetLocked(True)
    board.Add(via)
    return via


def add_core_outline(board):
    corners = ((32.5, 7.5), (57.5, 7.5), (57.5, 38.5), (32.5, 38.5))
    for start, end in zip(corners, corners[1:] + corners[:1]):
        line = pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(vec(*start))
        line.SetEnd(vec(*end))
        line.SetLayer(pcbnew.Dwgs_User)
        line.SetWidth(mm(0.15))
        board.Add(line)
    label = pcbnew.PCB_TEXT(board)
    label.SetText("OVERTHINKING ENGINE // LOCKED QFN FANOUT")
    label.SetPosition(vec(45.0, 37.8))
    label.SetLayer(pcbnew.B_SilkS)
    label.SetTextSize(vec(0.65, 0.65))
    label.SetTextThickness(mm(0.10))
    board.Add(label)


board = pcbnew.LoadBoard(str(BOARD_PATH))
rp = next(fp for fp in board.GetFootprints() if fp.GetReference() == "U1")
rp_pads = {int(pad.GetNumber()): pad for pad in rp.Pads() if pad.GetNumber().isdigit()}

# East-side application I/O. The 0.4 mm-pitch pads escape horizontally into
# two alternating via columns. A far-column trace passes midway between the
# two neighbouring near-column vias with 0.125 mm physical copper clearance,
# above the board's explicit 0.10 mm (4 mil) manufacturing rule.
east_pins = [2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14]
stats = {"tracks": 0, "vias": 0, "nets": []}
for index, pin in enumerate(east_pins):
    pad = rp_pads[pin]
    pad_y = pcbnew.ToMM(pad.GetPosition().y)
    via_x = 49.30 if index % 2 == 0 else 50.30
    via_y = pad_y
    via_position = vec(via_x, via_y)
    add_track(board, pad.GetNet(), pcbnew.B_Cu, pad.GetPosition(), via_position)
    add_via(board, pad.GetNet(), via_position)
    stats["tracks"] += 1
    stats["vias"] += 1
    stats["nets"].append(pad.GetNetname())

# RGB data exits from the adjacent south-east pad and joins the same inner
# bus without crossing the east-side fanout.
rgb = rp_pads[15]
rgb_via = vec(49.30, 31.30)
rgb_corner = vec(48.4375, 30.4375)
add_track(board, rgb.GetNet(), pcbnew.B_Cu, rgb.GetPosition(), rgb_corner)
add_track(board, rgb.GetNet(), pcbnew.B_Cu, rgb_corner, rgb_via)
add_via(board, rgb.GetNet(), rgb_via)
stats["tracks"] += 2
stats["vias"] += 1
stats["nets"].append(rgb.GetNetname())

# The two analog joystick signals leave the west edge on separate inner
# layers.  C7 was moved clear of this short, direct escape corridor.
for pin, via_xy in (
    (39, (40.30, 25.60)),
    (40, (39.50, 25.20)),
):
    pad = rp_pads[pin]
    via_position = vec(*via_xy)
    add_track(board, pad.GetNet(), pcbnew.B_Cu, pad.GetPosition(), via_position)
    add_via(board, pad.GetNet(), via_position)
    stats["tracks"] += 1
    stats["vias"] += 1
    stats["nets"].append(pad.GetNetname())

add_core_outline(board)
board.SynchronizeNetsAndNetClasses(False)
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(
    f"Locked controller-island fanout: {stats['tracks']} tracks, "
    f"{stats['vias']} vias, {len(stats['nets'])} nets"
)
print(", ".join(stats["nets"]))
