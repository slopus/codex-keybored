"""Print exact geometry for the remaining hand-routing DRC items."""

import json
import os
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"
DRC_PATH = Path(os.environ.get("CODEX_DRC", "/tmp/codex_small_drc.json"))


def point(position):
    return f"({pcbnew.ToMM(position.x):.4f},{pcbnew.ToMM(position.y):.4f})"


board = pcbnew.LoadBoard(str(BOARD_PATH))
connectivity = board.GetConnectivity()
connectivity.RecalculateRatsnest()
items = []
for footprint in board.GetFootprints():
    items.extend(footprint.Pads())
items.extend(board.GetTracks())
by_uuid = {item.m_Uuid.AsString(): item for item in items}

report = json.loads(DRC_PATH.read_text())
for index, issue in enumerate(report.get("unconnected_items", []), 1):
    if all("[GND]" in item.get("description", "") for item in issue.get("items", [])):
        continue
    print(f"\nISSUE {index}")
    for entry in issue["items"]:
        item = by_uuid.get(entry["uuid"])
        if item is None:
            print(f"  MISSING {entry['description']} {entry['uuid']}")
            continue
        if isinstance(item, pcbnew.PAD):
            print(
                f"  PAD {item.GetParentFootprint().GetReference()}.{item.GetNumber()} "
                f"net={item.GetNetname()} pos={point(item.GetPosition())} "
                f"layer={item.GetLayerName()} size={point(item.GetSize())} "
                f"uuid={entry['uuid']}"
            )
        elif isinstance(item, pcbnew.PCB_VIA):
            print(
                f"  VIA net={item.GetNetname()} pos={point(item.GetPosition())} "
                f"diam={pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)):.3f} "
                f"drill={pcbnew.ToMM(item.GetDrillValue()):.3f} uuid={entry['uuid']}"
            )
        else:
            print(
                f"  TRACK net={item.GetNetname()} layer={item.GetLayerName()} "
                f"start={point(item.GetStart())} end={point(item.GetEnd())} "
                f"width={pcbnew.ToMM(item.GetWidth()):.3f} uuid={entry['uuid']}"
            )

    resolved = [by_uuid.get(entry["uuid"]) for entry in issue["items"]]
    u1_pad = next(
        (
            item for item in resolved
            if isinstance(item, pcbnew.PAD)
            and item.GetParentFootprint().GetReference() == "U1"
        ),
        None,
    )
    other = next((item for item in resolved if item is not None and item is not u1_pad), None)
    if u1_pad is None or other is None:
        continue
    ux, uy = pcbnew.ToMM(u1_pad.GetPosition().x), pcbnew.ToMM(u1_pad.GetPosition().y)
    anchors = []
    for connected in connectivity.GetConnectedItems(other):
        candidates = []
        if isinstance(connected, pcbnew.PAD):
            candidates.append((connected.GetPosition(), connected.GetLayerName(), "PAD"))
        elif isinstance(connected, pcbnew.PCB_VIA):
            candidates.append((connected.GetPosition(), "THRU", "VIA"))
        elif isinstance(connected, pcbnew.PCB_TRACK):
            candidates.extend(
                (
                    (connected.GetStart(), connected.GetLayerName(), "TRACK"),
                    (connected.GetEnd(), connected.GetLayerName(), "TRACK"),
                )
            )
        for position, layer, kind in candidates:
            x, y = pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)
            distance = ((x - ux) ** 2 + (y - uy) ** 2) ** 0.5
            anchors.append((distance, x, y, layer, kind, connected.m_Uuid.AsString()))
    print(f"  OTHER COMPONENT: {len(connectivity.GetConnectedItems(other))} items")
    for distance, x, y, layer, kind, uuid in sorted(anchors)[:8]:
        print(
            f"    nearest {distance:.3f} mm: {kind} {layer} "
            f"({x:.4f},{y:.4f}) uuid={uuid}"
        )
