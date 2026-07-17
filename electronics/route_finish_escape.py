"""Regularize the last RP2040 fan-outs before final board-wide bridges.

KiCad's macOS SWIG wrapper invalidates track proxies after repeated removals,
so reviewed legacy dog-bones are removed as exact s-expression blocks first.
The replacement copper is then created through pcbnew in one save operation.
"""

from pathlib import Path
import re

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"


def close(a, b, tolerance=0.003):
    return abs(a[0] - b[0]) < tolerance and abs(a[1] - b[1]) < tolerance


def unordered_match(a1, a2, b1, b2):
    return (close(a1, b1) and close(a2, b2)) or (close(a1, b2) and close(a2, b1))


segment_removals = []


def remove_path(net_name, layer_name, points):
    for a, b in zip(points, points[1:]):
        segment_removals.append((net_name, layer_name, a, b))


remove_path("+1V1", "B.Cu", [(45.2, 23.5625), (45.2, 22.8), (44.8, 22.4), (44.8, 21.3)])
remove_path("+1V1", "In2.Cu", [(44.8, 21.3), (43.6, 21.3)])
remove_path("QSPI_SD3", "B.Cu", [(45.6, 23.5625), (45.6, 21.5)])
remove_path("QSPI_SD2", "B.Cu", [(46.0, 23.5625), (46.0, 22.8), (46.8, 22.0), (46.8, 21.2)])
remove_path("QSPI_SD2", "In2.Cu", [(46.8, 21.2), (50.75, 21.2)])
remove_path("QSPI_SD1", "B.Cu", [(46.4, 23.5625), (46.4, 23.1134), (46.8019, 22.7115)])

remove_path("XIN", "B.Cu", [(45.6, 30.4375), (45.6, 30.8039), (45.848, 31.0519), (48.1619, 31.0519), (48.7893, 31.6793)])
remove_path("+3V3", "B.Cu", [(44.8, 30.4375), (44.8, 30.8405), (45.3022, 31.3427), (47.1177, 31.3427), (47.775, 32.0)])
remove_path("+1V1", "B.Cu", [(44.4, 30.4375), (44.4, 31.1), (45.2, 31.9)])
remove_path("+1V1", "In2.Cu", [(45.2, 31.9), (44.1, 33.0)])
remove_path("+1V1", "In3.Cu", [(45.2, 31.9), (46.1747, 32.8747)])

via_removals = {
    ("+1V1", (44.8, 21.3)),
    ("QSPI_SD3", (45.6, 21.5)),
    ("QSPI_SD2", (46.8, 21.2)),
    ("QSPI_SD1", (46.8019, 22.7115)),
    ("+1V1", (45.2, 31.9)),
}


def top_level_copper_blocks(text):
    starts = [match.start() for match in re.finditer(r"(?m)^\t\((?:segment|via)\n", text)]
    for start in starts:
        depth = 0
        for index in range(start + 1, len(text)):
            char = text[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    if end < len(text) and text[end] == "\n":
                        end += 1
                    yield start, end, text[start:end]
                    break


def pair(block, field):
    match = re.search(rf"\({field}\s+(-?[0-9.]+)\s+(-?[0-9.]+)\)", block)
    return (float(match.group(1)), float(match.group(2))) if match else None


text = BOARD_PATH.read_text()
remove_ranges = []
matched_segments = set()
matched_vias = set()
for start, end, block in top_level_copper_blocks(text):
    net_match = re.search(r'\(net "([^"]+)"\)', block)
    if not net_match:
        continue
    net_name = net_match.group(1)
    if block.startswith("\t(segment"):
        layer_match = re.search(r'\(layer "([^"]+)"\)', block)
        a = pair(block, "start")
        b = pair(block, "end")
        if not layer_match or a is None or b is None:
            continue
        for index, (wanted_net, wanted_layer, wanted_a, wanted_b) in enumerate(segment_removals):
            if net_name == wanted_net and layer_match.group(1) == wanted_layer and unordered_match(a, b, wanted_a, wanted_b):
                remove_ranges.append((start, end))
                matched_segments.add(index)
                break
    else:
        position = pair(block, "at")
        for wanted in via_removals:
            if position is not None and net_name == wanted[0] and close(position, wanted[1]):
                remove_ranges.append((start, end))
                matched_vias.add(wanted)
                break

if len(matched_segments) != len(segment_removals) or len(matched_vias) != len(via_removals):
    raise RuntimeError(
        f"Legacy escape geometry changed: matched {len(matched_segments)}/{len(segment_removals)} "
        f"segments and {len(matched_vias)}/{len(via_removals)} vias"
    )
for start, end in sorted(remove_ranges, reverse=True):
    text = text[:start] + text[end:]
BOARD_PATH.write_text(text)


def mm(value):
    return pcbnew.FromMM(value)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_track(board, net_name, layer, a, b, width=0.15):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(vec(*a))
    track.SetEnd(vec(*b))
    track.SetLayer(layer)
    track.SetWidth(mm(width))
    track.SetNetCode(board.FindNet(net_name).GetNetCode())
    track.SetLocked(True)
    board.Add(track)


def add_path(board, net_name, layer, points):
    for a, b in zip(points, points[1:]):
        add_track(board, net_name, layer, a, b)


def add_via(board, net_name, position, size=0.45, drill=0.20):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(vec(*position))
    via.SetWidth(mm(size))
    via.SetDrill(mm(drill))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNetCode(board.FindNet(net_name).GetNetCode())
    via.SetLocked(True)
    board.Add(via)


board = pcbnew.LoadBoard(str(BOARD_PATH))
for reference, x, y, rotation in (
    ("C6", 53.0, 33.1, 0),
    ("C11", 54.0, 22.0, 90),
    ("C12", 54.0, 25.0, 90),
    ("C13", 54.0, 28.0, 90),
    ("C17", 56.0, 33.1, 0),
):
    footprint = next(fp for fp in board.GetFootprints() if fp.GetReference() == reference)
    footprint.SetPosition(vec(x, y))
    footprint.SetOrientationDegrees(rotation)
u1 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "U1")
pads = {int(p.GetNumber()): p for p in u1.Pads() if p.GetNumber().isdigit()}

# Regular 0.45/0.20 mm top-edge dog-bones.
top_fanout = (
    (47, "USB_DM_R", (44.0, 20.2)),
    (48, "USB_DP_R", (44.4, 21.0)),
    (49, "+3V3", (44.8, 19.4)),
    (50, "+1V1", (45.2, 20.2)),
    (51, "QSPI_SD3", (45.6, 21.0)),
    (52, "QSPI_SD2", (46.0, 19.4)),
    (53, "QSPI_SD1", (46.4, 20.2)),
    (54, "QSPI_SD0", (46.8, 21.0)),
)
for pin, net_name, via_xy in top_fanout:
    pad = pads[pin]
    start = (pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y))
    add_track(board, net_name, pcbnew.B_Cu, start, via_xy)
    add_via(board, net_name, via_xy)

add_path(board, "+1V1", pcbnew.In3_Cu, [(45.2, 20.2), (45.2, 18.4), (43.2, 18.4), (43.2, 21.3), (43.6, 21.3)])
# SD3 lands directly on its preserved In3 segment.
add_path(board, "QSPI_SD2", pcbnew.In2_Cu, [(46.0, 19.4), (50.75, 19.4), (50.75, 21.2)])
add_path(board, "QSPI_SD1", pcbnew.In2_Cu, [(46.4, 20.2), (47.6, 20.2), (47.6, 22.7115), (46.8019, 22.7115)])

# Regular south-edge fan-out.  Long XOUT and SWCLK links remain for A*.
south_fanout = (
    (20, "XIN", (45.6, 33.0)),
    (21, "XOUT", (45.2, 33.8)),
    (22, "+3V3", (44.8, 33.0)),
    (23, "+1V1", (44.4, 33.8)),
    (24, "SWCLK", (44.0, 33.0)),
)
for pin, net_name, via_xy in south_fanout:
    pad = pads[pin]
    start = (pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y))
    add_track(board, net_name, pcbnew.B_Cu, start, via_xy)
    add_via(board, net_name, via_xy)

add_path(board, "XIN", pcbnew.In3_Cu, [(45.6, 33.0), (47.0, 33.0), (48.7893, 31.6793)])
add_via(board, "+3V3", (47.775, 32.0))
add_path(board, "+3V3", pcbnew.In4_Cu, [(44.8, 33.0), (47.775, 32.0)])
add_path(board, "+1V1", pcbnew.In2_Cu, [(44.4, 33.8), (44.1, 33.0)])
add_path(board, "+1V1", pcbnew.In3_Cu, [(44.4, 33.8), (46.1747, 32.8747)])

# A7/B7 require a layer hop around the already-routed D+ U-shape.  The
# 0.40/0.20 mm vias sit in the long connector lands, with 0.15 mm copper
# clearance to the neighbouring D+ pads.  They must be tented from B.Cu.
add_via(board, "USB_DM_CONN", (45.25, 1.055), size=0.40)
add_track(board, "USB_DM_CONN", pcbnew.In2_Cu, (45.25, 1.055), (44.25, 1.055))
add_via(board, "USB_DM_CONN", (44.25, 1.055), size=0.40)

board.SynchronizeNetsAndNetClasses(False)
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(
    f"Replaced {len(segment_removals)} segments/{len(via_removals)} vias; "
    "installed regular top/south QFN escapes and USB-C D- crossover"
)
