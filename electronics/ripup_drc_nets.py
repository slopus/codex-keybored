"""Rip up only nets implicated by the latest connectivity/critical DRC report."""

import json
import os
import re
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"
DRC_PATH = Path(os.environ.get(
    "CODEX_DRC_PATH",
    ROOT / "production" / "codex_micro_wired_revA_drc.json",
))
CRITICAL_TYPES = {
    "shorting_items", "clearance", "tracks_crossing", "hole_clearance",
    "copper_edge_clearance", "via_dangling", "hole_to_hole",
}


def item_nets(item):
    return {
        match for match in re.findall(r"\[([^]]*)\]", item.get("description", ""))
        if match and match != "<no net>"
    }


explicit_nets = os.environ.get("CODEX_RIPUP_NETS", "").strip()
if explicit_nets:
    nets = {name.strip() for name in explicit_nets.split(",") if name.strip()}
else:
    report = json.loads(DRC_PATH.read_text())
    nets = set()
    for issue in report.get("unconnected_items", []):
        for item in issue.get("items", []):
            nets.update(item_nets(item))
    for issue in report.get("violations", []):
        if issue.get("type") not in CRITICAL_TYPES:
            continue
        for item in issue.get("items", []):
            nets.update(item_nets(item))
nets -= {
    name.strip() for name in os.environ.get("CODEX_KEEP_NETS", "").split(",")
    if name.strip()
}

board = pcbnew.LoadBoard(str(BOARD_PATH))
tracks = list(board.GetTracks())
removed = 0
for track in tracks:
    if track.GetNetname() in nets:
        board.Remove(track)
        removed += 1
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Ripped up {removed} tracks/vias across {len(nets)} nets: {', '.join(sorted(nets))}")
