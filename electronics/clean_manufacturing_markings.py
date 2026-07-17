"""Keep only intentional board text on manufactured silkscreen layers."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"


def mm(value):
    return pcbnew.FromMM(value)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


board = pcbnew.LoadBoard(str(BOARD_PATH))
layer_cleanup = {
    pcbnew.F_CrtYd: pcbnew.F_Fab,
    pcbnew.B_CrtYd: pcbnew.B_Fab,
    pcbnew.F_SilkS: pcbnew.F_Fab,
    pcbnew.B_SilkS: pcbnew.B_Fab,
}
for footprint in board.GetFootprints():
    for graphic in footprint.GraphicalItems():
        if graphic.GetLayer() in layer_cleanup:
            graphic.SetLayer(layer_cleanup[graphic.GetLayer()])

updates = {
    "CODEX KEYBORED": (45.0, 87.4, 1.1, False),
    "WORK LOAFER EDITION // REV A2": (45.0, 85.7, 0.8, False),
    "JOY: ALPS RKJXY 4-WIRE FFC": (73.6, 27.5, 0.8, False),
    "ENC": (16.4, 28.4, 0.8, False),
    "LQFP48 / CRYSTAL-LESS USB / PRESS KEYS, SHIP BUGS": (45.0, 89.0, 0.8, True),
}
for drawing in board.GetDrawings():
    if not isinstance(drawing, pcbnew.PCB_TEXT) or drawing.GetText() not in updates:
        continue
    x, y, size, mirrored = updates[drawing.GetText()]
    drawing.SetPosition(vec(x, y))
    drawing.SetTextSize(vec(size, size))
    drawing.SetTextThickness(mm(0.15))
    drawing.SetMirrored(mirrored)

pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Moved stock footprint ink/courtyards to Fab and normalized parody silkscreen")
