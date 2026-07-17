"""Import a Freerouting SES session and save the routed KiCad board."""

from pathlib import Path
import re
import os
import pcbnew

root = Path("/Users/steve/Documents/CodexKB/codex-micro/electronics/kicad")
source = root / "codex_micro_wired_revA.kicad_pcb"
session = root / os.environ.get(
    "CODEX_SES", "codex_micro_wired_revA_route_signals.ses"
)


def remove_duplicate_via_padstack(path: Path) -> None:
    """Work around duplicate library_out padstacks emitted by Freerouting 1.9."""
    text = path.read_text()
    marker_match = re.search(r'^[ \t]*\(padstack "Via\[0-5\]_\d+:\d+_um"', text, re.MULTILINE)
    if marker_match is None:
        return
    marker = marker_match.group(0)
    starts = []
    cursor = 0
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            break
        starts.append(start)
        cursor = start + len(marker)
    if len(starts) < 2:
        return

    def balanced_block(start: int):
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    if end < len(text) and text[end] == "\n":
                        end += 1
                    return text[start:end], end
        raise RuntimeError("Unbalanced SES padstack block")

    first, _ = balanced_block(starts[0])
    second, second_end = balanced_block(starts[1])
    if first != second:
        raise RuntimeError("Freerouting emitted two non-identical via padstacks")
    path.write_text(text[:starts[1]] + text[second_end:])
    print("Removed duplicate Freerouting via padstack definition")


remove_duplicate_via_padstack(session)
board = pcbnew.LoadBoard(str(source))
existing_tracks = list(board.GetTracks())
existing_zones = list(board.Zones())
for track in existing_tracks:
    # Preserve the hand-routed, locked RP2040 fan-out.  Freerouting treats
    # those items as fixed obstacles and therefore does not repeat them in
    # network_out.  Removing only unlocked copper also keeps re-imports
    # deterministic instead of accumulating duplicate auto-routed paths.
    if not track.IsLocked():
        board.Remove(track)
for zone in existing_zones:
    board.Remove(zone)

# KiCad 10 rejects some otherwise valid Freerouting SES files when a DSN
# uses named power layers. Import the deterministic routing subset directly:
# straight path vertices and through-vias. Coordinates use 10 database units
# per micrometre and inverted Y. The SES describes the complete signal routing,
# so previous unlocked tracks/zones are removed before rebuilding it.
if True:
    print("Using verified SES path importer")
    layer_map = {
        "F.Cu": pcbnew.F_Cu,
        "GND_PLANE": pcbnew.In1_Cu,
        "SIGNAL_1": pcbnew.In2_Cu,
        "SIGNAL_2": pcbnew.In3_Cu,
        "+5V_PLANE": pcbnew.In4_Cu,
        "B.Cu": pcbnew.B_Cu,
    }
    resolution = 10.0

    def coord(x, y):
        return pcbnew.VECTOR2I(
            pcbnew.FromMM(float(x) / resolution / 1000.0),
            pcbnew.FromMM(-float(y) / resolution / 1000.0),
        )

    text = session.read_text().splitlines()
    in_network = False
    current_net = None
    current_layer = None
    current_width = None
    vertices = []
    stats = {"tracks": 0, "vias": 0}

    def commit_path():
        global vertices
        if current_net is None or current_layer is None or len(vertices) < 2:
            vertices = []
            return
        net = board.FindNet(current_net)
        if net is None:
            raise RuntimeError(f"SES references unknown net {current_net}")
        for start, end in zip(vertices, vertices[1:]):
            if start == end:
                continue
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(start)
            track.SetEnd(end)
            track.SetLayer(layer_map[current_layer])
            track.SetWidth(pcbnew.FromMM(current_width / resolution / 1000.0))
            track.SetNet(net)
            board.Add(track)
            stats["tracks"] += 1
        vertices = []

    for raw in text:
        stripped = raw.strip()
        if stripped == "(network_out":
            in_network = True
            continue
        if not in_network:
            continue
        net_match = re.fullmatch(r"\(net\s+(.+)", stripped)
        if net_match:
            commit_path()
            current_net = net_match.group(1).strip('"')
            continue
        path_match = re.fullmatch(r"\(path\s+(\S+)\s+(\d+)", stripped)
        if path_match:
            commit_path()
            # Freerouting 2.x quotes named inner layers in SES paths, while
            # 1.9 emitted the same names without quotes.
            current_layer = path_match.group(1).strip('"')
            current_width = float(path_match.group(2))
            if current_layer not in layer_map:
                raise RuntimeError(f"Unknown SES layer {current_layer}")
            continue
        vertex_match = re.fullmatch(r"(-?\d+)\s+(-?\d+)", stripped)
        if vertex_match and current_layer is not None:
            vertices.append(coord(vertex_match.group(1), vertex_match.group(2)))
            continue
        via_match = re.fullmatch(
            r'\(via\s+"Via\[0-5\]_(\d+):(\d+)_um"\s+(-?\d+)\s+(-?\d+)',
            stripped,
        )
        if via_match:
            commit_path()
            if current_net is None:
                raise RuntimeError("SES via appeared before a net")
            net = board.FindNet(current_net)
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(coord(via_match.group(3), via_match.group(4)))
            via.SetWidth(pcbnew.FromMM(float(via_match.group(1)) / 1000.0))
            via.SetDrill(pcbnew.FromMM(float(via_match.group(2)) / 1000.0))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(net)
            board.Add(via)
            stats["vias"] += 1
            continue
        if stripped == ")" and current_layer is not None and vertices:
            commit_path()
            current_layer = None
            current_width = None

    commit_path()
    if stats["tracks"] == 0:
        raise RuntimeError("Fallback SES importer found no tracks")
    print(f"Imported {stats['tracks']} routed segments and {stats['vias']} vias")
pcbnew.SaveBoard(str(source), board)
print(source)
