"""Route the remaining non-GND ratsnest edges with a deterministic 3D A* grid."""

from heapq import heappop, heappush
import json
import math
import os
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"
DRC_PATH = Path(os.environ.get("CODEX_DRC", ROOT / "production" / "codex_micro_wired_revA_drc.json"))
GRID = float(os.environ.get("CODEX_GRID", "0.25"))
TRACK_MARGIN = float(os.environ.get("CODEX_TRACK_MARGIN", "0.25"))
VIA_MARGIN = float(os.environ.get("CODEX_VIA_MARGIN", "0.45"))
EDGE_TRACK = float(os.environ.get("CODEX_EDGE_TRACK", "0.45"))
EDGE_VIA = float(os.environ.get("CODEX_EDGE_VIA", "0.45"))
SIZE = int(90 / GRID) + 1
ROUTE_LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
LAYER_INDEX = {layer: index for index, layer in enumerate(ROUTE_LAYERS)}


def mm(value):
    return pcbnew.FromMM(value)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def xy_mm(position):
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def grid_xy(position):
    x, y = xy_mm(position)
    return round(x / GRID), round(y / GRID)


def state_id(layer_index, x, y):
    return (layer_index * SIZE + y) * SIZE + x


def decode(state):
    x = state % SIZE
    value = state // SIZE
    y = value % SIZE
    layer_index = value // SIZE
    return layer_index, x, y


def item_anchors(item):
    anchors = []
    if isinstance(item, pcbnew.PCB_VIA):
        x, y = grid_xy(item.GetPosition())
        for layer_index in range(len(ROUTE_LAYERS)):
            anchors.append((state_id(layer_index, x, y), item.GetPosition()))
    elif isinstance(item, pcbnew.PCB_TRACK):
        layer_index = LAYER_INDEX.get(item.GetLayer())
        if layer_index is not None:
            for position in (item.GetStart(), item.GetEnd()):
                x, y = grid_xy(position)
                anchors.append((state_id(layer_index, x, y), position))
    elif isinstance(item, pcbnew.PAD):
        x, y = grid_xy(item.GetPosition())
        if item.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            for layer_index in range(len(ROUTE_LAYERS)):
                anchors.append((state_id(layer_index, x, y), item.GetPosition()))
        else:
            layer = pcbnew.B_Cu if item.GetLayerSet().Contains(pcbnew.B_Cu) else pcbnew.F_Cu
            if layer in LAYER_INDEX:
                anchors.append((state_id(LAYER_INDEX[layer], x, y), item.GetPosition()))
    return anchors


def component_anchors(connectivity, representative):
    anchors = []
    for item in connectivity.GetConnectedItems(representative):
        anchors.extend(item_anchors(item))
    return anchors


def add_track(board, net, layer, start, end):
    if start == end:
        return
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start)
    track.SetEnd(end)
    track.SetLayer(layer)
    track.SetWidth(mm(0.20))
    track.SetNet(net)
    board.Add(track)


def mark_disc(blocked, layers, cx, cy, radius):
    x0 = max(0, int(math.floor((cx - radius) / GRID)))
    x1 = min(SIZE - 1, int(math.ceil((cx + radius) / GRID)))
    y0 = max(0, int(math.floor((cy - radius) / GRID)))
    y1 = min(SIZE - 1, int(math.ceil((cy + radius) / GRID)))
    radius2 = radius * radius
    for x in range(x0, x1 + 1):
        gx = x * GRID
        for y in range(y0, y1 + 1):
            gy = y * GRID
            if (gx - cx) ** 2 + (gy - cy) ** 2 <= radius2:
                for layer_index in layers:
                    blocked.add(state_id(layer_index, x, y))


def build_blocked(board, current_net):
    blocked = set()
    via_blocked = set()
    all_layers = range(len(ROUTE_LAYERS))

    # Board perimeter and reverse-mount LED center windows.
    for x in range(SIZE):
        for y in range(SIZE):
            coordinate_x = x * GRID
            coordinate_y = y * GRID
            if (
                coordinate_x < EDGE_TRACK or coordinate_x > 90 - EDGE_TRACK
                or coordinate_y < EDGE_TRACK or coordinate_y > 90 - EDGE_TRACK
            ):
                for layer_index in all_layers:
                    blocked.add(state_id(layer_index, x, y))
            if (
                coordinate_x < EDGE_VIA or coordinate_x > 90 - EDGE_VIA
                or coordinate_y < EDGE_VIA or coordinate_y > 90 - EDGE_VIA
            ):
                for layer_index in all_layers:
                    via_blocked.add(state_id(layer_index, x, y))
    for footprint in board.GetFootprints():
        if footprint.GetReference().startswith("LED"):
            cx, cy = xy_mm(footprint.GetPosition())
            mark_disc(blocked, all_layers, cx, cy, 1.90)
            mark_disc(via_blocked, all_layers, cx, cy, 1.90)

    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() == current_net and pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                continue
            box = pad.GetBoundingBox()
            left = pcbnew.ToMM(box.GetLeft()) - TRACK_MARGIN
            right = pcbnew.ToMM(box.GetRight()) + TRACK_MARGIN
            top = pcbnew.ToMM(box.GetTop()) - TRACK_MARGIN
            bottom = pcbnew.ToMM(box.GetBottom()) + TRACK_MARGIN
            x0 = max(0, int(math.floor(left / GRID)))
            x1 = min(SIZE - 1, int(math.ceil(right / GRID)))
            y0 = max(0, int(math.floor(top / GRID)))
            y1 = min(SIZE - 1, int(math.ceil(bottom / GRID)))
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                layers = all_layers
            else:
                layer = pcbnew.B_Cu if pad.GetLayerSet().Contains(pcbnew.B_Cu) else pcbnew.F_Cu
                layers = (LAYER_INDEX[layer],) if layer in LAYER_INDEX else ()
            for layer_index in layers:
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        blocked.add(state_id(layer_index, x, y))

            # A 0.60 mm through-via needs 0.15 mm clearance around its
            # copper, hence a 0.45 mm center keepout from the pad outline.
            via_left = pcbnew.ToMM(box.GetLeft()) - VIA_MARGIN
            via_right = pcbnew.ToMM(box.GetRight()) + VIA_MARGIN
            via_top = pcbnew.ToMM(box.GetTop()) - VIA_MARGIN
            via_bottom = pcbnew.ToMM(box.GetBottom()) + VIA_MARGIN
            vx0 = max(0, int(math.floor(via_left / GRID)))
            vx1 = min(SIZE - 1, int(math.ceil(via_right / GRID)))
            vy0 = max(0, int(math.floor(via_top / GRID)))
            vy1 = min(SIZE - 1, int(math.ceil(via_bottom / GRID)))
            for layer_index in layers:
                for x in range(vx0, vx1 + 1):
                    for y in range(vy0, vy1 + 1):
                        via_blocked.add(state_id(layer_index, x, y))

    for item in board.GetTracks():
        if item.GetNetname() == current_net:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            cx, cy = xy_mm(item.GetPosition())
            other_radius = pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)) / 2
            mark_disc(blocked, all_layers, cx, cy, other_radius + TRACK_MARGIN)
            mark_disc(via_blocked, all_layers, cx, cy, other_radius + VIA_MARGIN)
            continue
        layer_index = LAYER_INDEX.get(item.GetLayer())
        if layer_index is None:
            continue
        x1, y1 = xy_mm(item.GetStart())
        x2, y2 = xy_mm(item.GetEnd())
        length = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(math.ceil(length / (GRID / 2))))
        radius = pcbnew.ToMM(item.GetWidth()) / 2 + TRACK_MARGIN
        via_radius = pcbnew.ToMM(item.GetWidth()) / 2 + VIA_MARGIN
        for index in range(steps + 1):
            t = index / steps
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t
            mark_disc(
                blocked, (layer_index,),
                cx, cy, radius,
            )
            mark_disc(via_blocked, (layer_index,), cx, cy, via_radius)
    return blocked, via_blocked


def heuristic(state, goals):
    layer_index, x, y = decode(state)
    return min(
        abs(x - gx) + abs(y - gy) + 8 * abs(layer_index - glayer)
        for glayer, gx, gy in goals
    )


def route_astar(blocked, via_blocked, starts, goals):
    goal_states = {state for state, _ in goals}
    goal_decoded = [decode(state) for state in goal_states]
    queue = []
    parent = {}
    score = {}
    start_lookup = {}
    for state, position in starts:
        blocked.discard(state)
        if state not in score:
            score[state] = 0.0
            start_lookup[state] = position
            heappush(queue, (heuristic(state, goal_decoded), 0.0, state))
    for state in goal_states:
        blocked.discard(state)

    reached = None
    while queue:
        _, cost, state = heappop(queue)
        if cost != score.get(state):
            continue
        if state in goal_states:
            reached = state
            break
        layer_index, x, y = decode(state)
        neighbours = []
        for dx, dy in (
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ):
            nx, ny = x + dx, y + dy
            if 0 <= nx < SIZE and 0 <= ny < SIZE:
                if dx and dy:
                    # Do not cut diagonally across the corner of an obstacle.
                    if (
                        state_id(layer_index, x + dx, y) in blocked
                        or state_id(layer_index, x, y + dy) in blocked
                    ):
                        continue
                    step = math.sqrt(2)
                else:
                    step = 1.0
                neighbours.append((state_id(layer_index, nx, ny), step))
        for next_layer in range(len(ROUTE_LAYERS)):
            if next_layer != layer_index:
                # A through-via crosses every copper layer, so the location must
                # be clear on every routable signal layer, not only on its two
                # endpoints.  This avoids the hidden inner-layer shorts that a
                # normal 2-D grid check would miss.
                if not any(
                    state_id(candidate_layer, x, y) in via_blocked
                    for candidate_layer in range(len(ROUTE_LAYERS))
                ):
                    neighbours.append((state_id(next_layer, x, y), 14.0 + 2 * abs(next_layer - layer_index)))
        for neighbour, step in neighbours:
            if neighbour in blocked:
                continue
            new_cost = cost + step
            if new_cost < score.get(neighbour, float("inf")):
                score[neighbour] = new_cost
                parent[neighbour] = state
                heappush(queue, (new_cost + heuristic(neighbour, goal_decoded), new_cost, neighbour))

    if reached is None:
        raise RuntimeError("A* could not find a route")
    path = [reached]
    while path[-1] in parent:
        path.append(parent[path[-1]])
    path.reverse()
    start_state = path[0]
    goal_position = next(position for state, position in goals if state == reached)
    return path, start_lookup[start_state], goal_position


def materialize(board, net, path, start_position, goal_position):
    decoded = [decode(state) for state in path]
    start_layer = ROUTE_LAYERS[decoded[0][0]]
    start_grid = vec(decoded[0][1] * GRID, decoded[0][2] * GRID)
    add_track(board, net, start_layer, start_position, start_grid)

    segment_start = start_grid
    previous_direction = None
    for index in range(1, len(decoded)):
        prev_layer, prev_x, prev_y = decoded[index - 1]
        layer_index, x, y = decoded[index]
        previous_point = vec(prev_x * GRID, prev_y * GRID)
        point_now = vec(x * GRID, y * GRID)
        if layer_index != prev_layer:
            if segment_start != previous_point:
                add_track(board, net, ROUTE_LAYERS[prev_layer], segment_start, previous_point)
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(previous_point)
            via.SetWidth(mm(0.60))
            via.SetDrill(mm(0.30))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(net)
            board.Add(via)
            segment_start = point_now
            previous_direction = None
            continue
        direction = (x - prev_x, y - prev_y)
        if previous_direction is not None and direction != previous_direction:
            add_track(board, net, ROUTE_LAYERS[layer_index], segment_start, previous_point)
            segment_start = previous_point
        previous_direction = direction

    end_layer, end_x, end_y = decoded[-1]
    end_grid = vec(end_x * GRID, end_y * GRID)
    if segment_start != end_grid:
        add_track(board, net, ROUTE_LAYERS[end_layer], segment_start, end_grid)
    add_track(board, net, ROUTE_LAYERS[end_layer], end_grid, goal_position)


board = pcbnew.LoadBoard(str(BOARD_PATH))
report = json.loads(DRC_PATH.read_text())
issues = [
    issue for issue in report.get("unconnected_items", [])
    if not any("[GND]" in item.get("description", "") for item in issue.get("items", []))
]
routed = 0
for issue in issues:
    # Refresh item UUID mapping and connectivity after every new bridge.
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    items = []
    for footprint in board.GetFootprints():
        items.extend(footprint.Pads())
    items.extend(board.GetTracks())
    by_uuid = {item.m_Uuid.AsString(): item for item in items}
    first = by_uuid.get(issue["items"][0]["uuid"])
    second = by_uuid.get(issue["items"][1]["uuid"])
    if first is None or second is None:
        continue
    first_component = connectivity.GetConnectedItems(first)
    if any(item.m_Uuid.AsString() == second.m_Uuid.AsString() for item in first_component):
        continue
    net_name = first.GetNetname()
    if not net_name or net_name == "GND" or second.GetNetname() != net_name:
        continue
    starts = component_anchors(connectivity, first)
    goals = component_anchors(connectivity, second)
    blocked, via_blocked = build_blocked(board, net_name)
    try:
        path, start_position, goal_position = route_astar(blocked, via_blocked, starts, goals)
    except RuntimeError:
        print(f"Skipped {net_name}: no route on the current 0.25 mm grid")
        continue
    materialize(board, board.FindNet(net_name), path, start_position, goal_position)
    routed += 1
    print(f"Bridged {net_name}: {len(path)} grid states")

pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Added {routed} deterministic ratsnest bridges")
