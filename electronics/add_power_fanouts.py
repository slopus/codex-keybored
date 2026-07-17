"""Fan out SMD +5 V/+3V3 pads to their dedicated internal planes."""

from math import hypot
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"
POWER_NET_NAMES = {"+5V", "+3V3"}


def mm(value):
    return pcbnew.FromMM(value)


def point(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def point_mm(item):
    pos = item.GetPosition()
    return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)


def add_track(board, net, layer, start, end, width=0.20):
    if start == end:
        return
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start)
    track.SetEnd(end)
    track.SetLayer(layer)
    track.SetWidth(mm(width))
    track.SetNet(net)
    board.Add(track)


board = pcbnew.LoadBoard(str(BOARD_PATH))

# Idempotent rebuild. The signal-only router never emits these nets, so every
# existing +5 V/+3V3 track or via belongs to this deterministic post-process.
existing_tracks = list(board.GetTracks())
signal_items = [item for item in existing_tracks if item.GetNetname() not in POWER_NET_NAMES]
for item in existing_tracks:
    if item.GetNetname() in POWER_NET_NAMES:
        board.Remove(item)

all_pads = [pad for fp in board.GetFootprints() for pad in fp.Pads()]
groups = {}

for footprint in board.GetFootprints():
    fx, fy = point_mm(footprint)
    for pad in footprint.Pads():
        if (
            pad.GetNetname() not in POWER_NET_NAMES
            or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD
        ):
            continue
        px, py = point_mm(pad)
        if footprint.GetReference() == "J1":
            direction = (0, 1)
            side = "B"
        else:
            dx, dy = px - fx, py - fy
            if abs(dx) >= abs(dy):
                direction = (1 if dx >= 0 else -1, 0)
                side = "R" if dx >= 0 else "L"
            else:
                direction = (0, 1 if dy >= 0 else -1)
                side = "B" if dy >= 0 else "T"
        layer = pcbnew.B_Cu if pad.GetLayerSet().Contains(pcbnew.B_Cu) else pcbnew.F_Cu
        key = (footprint.GetReference(), pad.GetNetname(), side, layer)
        groups.setdefault(key, []).append((pad, px, py, direction))


def position_is_clear(candidate, net_name):
    cx, cy = pcbnew.ToMM(candidate.x), pcbnew.ToMM(candidate.y)
    if not (0.65 <= cx <= 89.35 and 0.65 <= cy <= 89.35):
        return False
    for pad in all_pads:
        if pad.GetNetname() == net_name:
            continue
        if pad.HitTest(candidate, mm(0.47)):
            return False
    for item in signal_items:
        if item.GetNetname() == net_name:
            continue
        if item.HitTest(candidate, mm(0.47)):
            return False
    return True


fanout_tracks = 0
fanout_vias = 0
for (reference, net_name, side, layer), entries in sorted(groups.items()):
    # Split adjacent same-net pads into compact clusters. This collapses RP2040
    # multi-pad supply banks to one via without ever bridging across USB data
    # or CC pads between the two VBUS pad pairs.
    tangent_index = 1 if side in ("L", "R") else 0
    entries.sort(key=lambda entry: (entry[1], entry[2])[tangent_index])
    clusters = []
    for entry in entries:
        tangent = (entry[1], entry[2])[tangent_index]
        if not clusters:
            clusters.append([entry])
            continue
        previous = (clusters[-1][-1][1], clusters[-1][-1][2])[tangent_index]
        if abs(tangent - previous) <= 0.61:
            clusters[-1].append(entry)
        else:
            clusters.append([entry])

    net = board.FindNet(net_name)
    for cluster in clusters:
        unique = []
        seen = set()
        for _, x, y, direction in cluster:
            key = (round(x, 5), round(y, 5))
            if key not in seen:
                unique.append((x, y))
                seen.add(key)
        direction = cluster[0][3]
        # Join only immediately adjacent supply pads on the same package edge.
        for first, second in zip(unique, unique[1:]):
            add_track(board, net, layer, point(*first), point(*second))
            fanout_tracks += 1

        sx = sum(x for x, _ in unique) / len(unique)
        sy = sum(y for _, y in unique) / len(unique)
        dx, dy = direction
        candidate = None
        for route_dx, route_dy in ((dx, dy), (-dy, dx), (dy, -dx), (-dx, -dy)):
            tx, ty = -route_dy, route_dx
            for distance in (0.90, 1.15, 1.45, 1.80, 2.20, 2.60, 3.00):
                for tangent_shift in (
                    0, 0.45, -0.45, 0.90, -0.90,
                    1.35, -1.35, 1.80, -1.80, 2.40, -2.40,
                ):
                    proposed = point(
                        sx + route_dx * distance + tx * tangent_shift,
                        sy + route_dy * distance + ty * tangent_shift,
                    )
                    if position_is_clear(proposed, net_name):
                        candidate = proposed
                        break
                if candidate is not None:
                    break
            if candidate is not None:
                break
        if candidate is None:
            raise RuntimeError(f"No fan-out via location for {reference} {net_name} {side}")

        source = point(sx, sy)
        add_track(board, net, layer, source, candidate)
        fanout_tracks += 1
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(candidate)
        via.SetWidth(mm(0.60))
        via.SetDrill(mm(0.30))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(net)
        board.Add(via)
        signal_items.append(via)
        fanout_vias += 1

pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Added {fanout_tracks} power fan-out tracks and {fanout_vias} plane vias")
