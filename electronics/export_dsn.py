"""Export the generated KiCad board to Specctra DSN for Freerouting."""

from pathlib import Path
import pcbnew

root = Path("/Users/steve/Documents/CodexKB/codex-micro/electronics/kicad")
board = pcbnew.LoadBoard(str(root / "codex_micro_wired_revA.kicad_pcb"))
if not pcbnew.ExportSpecctraDSN(board, str(root / "codex_micro_wired_revA.dsn")):
    raise RuntimeError("Specctra DSN export failed")
print(root / "codex_micro_wired_revA.dsn")
