"""Generate JLCPCB BOM/CPL files and a hand-assembly list from the KiCad PCB."""

from collections import defaultdict
import csv
from pathlib import Path
import re

import pcbnew


ROOT = Path("/Users/steve/Documents/CodexKB/codex-micro/electronics")
BOARD_PATH = ROOT / "kicad" / "codex_micro_wired_revA.kicad_pcb"
OUT = ROOT / "production"


PARTS = {
    "U1": ("STM32F072CBT6 128KB crystal-less USB", "STM32F072CBT6", "C81720"),
    "U3": ("ME6211C33M5G-N", "ME6211C33M5G-N", "C82942"),
    "U4": ("USBLC6-2SC6", "USBLC6-2SC6", "C7519"),
    "U5": ("SN74AHCT1G125DBVR", "SN74AHCT1G125DBVR", "C7484"),
    "U6": ("TTP223-BA6-TD", "TTP223-BA6-TD", "C42422127"),
    "J1": ("TYPE-C-31-M-12", "TYPE-C-31-M-12", "C165948"),
    "C19": ("CL32A107MQVNNNE 100uF 6.3V", "CL32A107MQVNNNE", "C49066"),
}


def natural_key(text):
    return [int(piece) if piece.isdigit() else piece for piece in re.split(r"(\d+)", text)]


def part_for(ref):
    if ref in PARTS:
        return PARTS[ref]
    if re.fullmatch(r"D(?:[1-9]|1[0-2])", ref):
        return ("1N4148W", "1N4148W", "C81598")
    if re.fullmatch(r"LED(?:[1-9]|1\d|2[0-4])", ref):
        return ("SK6812MINI-E", "SK6812MINI-E", "C5149201")
    if ref in {"R1", "R2"}:
        return ("5.1k 1% 0603", "0603WAF5101T5E", "C23186")
    if ref in {"R3", "R4"}:
        # C25804 was short during the 2026-07-17 JLC quote.  C98220 is the
        # same 0603 / 10 kOhm / 1% electrical class and had ample JLC stock.
        return ("10k 1% 0603", "RC0603FR-0710KL", "C98220")
    if ref in {"C1", "C2"}:
        return ("10uF 10V X5R 0603", "CL10A106KP8NNNC", "C19702")
    if ref in {"C3", "C4", "C5", "C6", "C7"}:
        return ("100nF 16V X7R 0402", "CL05B104KO5NNNC", "C1525")
    if ref == "C8":
        return ("1uF 10V X5R 0402", "CL05A105KP5NNNC", "C52923")
    if ref == "C9":
        return ("4.7uF 10V X5R 0603", "CL10A475KO8NNNC", "C19666")
    if ref == "C10":
        return ("100nF 50V X7R 0603", "CC0603KRX7R9BB104", "C14663")
    return None


HAND_PARTS = {
    **{f"SW{i}": ("Gateron KS-33 / Work Louder wrk.LP1", 1) for i in range(1, 13)},
    "SW13": ("TL3342-compatible RESET button, optional", 1),
    "SW14": ("TL3342-compatible BOOTSEL button, optional", 1),
    "ENC1": ("Clickable vertical encoder, 6 mm shaft; qualify against dial", 1),
    "JOY1": ("Alps Alpine RKJXY100000A or qualified clone", 1),
    "J2": ("Molex 200528-0040 4-way 1.0 mm FFC, if joystick tail requires it", 1),
}

# The quoted bottom-only assembly deliberately omits these parts.  The turnkey
# package below is a separate Standard PCBA / both-sides input set for JLC's
# consigned-parts and manual through-hole services.  It produces one finished
# primary board plus one electrically identical spare without asking the end
# user to solder anything.
TURNKEY_PARTS = {
    **{
        f"SW{i}": {
            "comment": "wrk. LP1 low-profile mechanical switch / customer consigned",
            "mpn": "WRK-LP1",
            "lcsc": "",
            "footprint": "Gateron low-profile footprint",
        }
        for i in range(1, 13)
    },
    "ENC1": {
        "comment": "Clickable vertical encoder 18 detents / 9 pulses",
        "mpn": "EC11E09444A8",
        "lcsc": "C1322538",
        "footprint": "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm_MountingHoles",
    },
    "JOY1": {
        "comment": "Alps ThumbPointer with knob / customer consigned",
        "mpn": "RKJXY1000006",
        "lcsc": "",
        "footprint": "Alps_RKJXY100000A_MECHANICAL",
    },
    "J2": {
        "comment": "4-position 1.0 mm bottom-contact FFC connector",
        "mpn": "200528-0040",
        "lcsc": "",
        "footprint": "Molex_200528-0040_1x04-1MP_P1.00mm_Horizontal",
    },
    "SW13": {
        "comment": "RESET factory-programming button",
        "mpn": "TL3342F160QG",
        "lcsc": "C2886898",
        "footprint": "SW_SPST_TL3342",
    },
    "SW14": {
        "comment": "BOOT0 factory-programming button",
        "mpn": "TL3342F160QG",
        "lcsc": "C2886898",
        "footprint": "SW_SPST_TL3342",
    },
}


board = pcbnew.LoadBoard(str(BOARD_PATH))
assembled = []
hand = []

for fp in board.GetFootprints():
    ref = fp.GetReference()
    if fp.IsDNP():
        if ref in HAND_PARTS:
            hand.append((ref, *HAND_PARTS[ref]))
        continue
    part = part_for(ref)
    if part is None:
        raise RuntimeError(f"No JLC/LCSC mapping for assembled footprint {ref}")
    comment, mpn, lcsc = part
    pos = fp.GetPosition()
    assembled.append({
        "ref": ref,
        "comment": comment,
        "mpn": mpn,
        "lcsc": lcsc,
        "footprint": fp.GetFPID().GetUniStringLibId(),
        "x": pcbnew.ToMM(pos.x),
        "y": pcbnew.ToMM(pos.y),
        "layer": "Bottom" if fp.IsFlipped() else "Top",
        "rotation": fp.GetOrientationDegrees() % 360,
    })

assembled.sort(key=lambda row: natural_key(row["ref"]))
# The current JLC cart intentionally uses bottom-side-only assembly. J1 is a
# fitted top-side USB-C connector, so keep it in BOM/CPL for a future both-side
# order but also call it out explicitly in the hand-soldering handoff.
for row in assembled:
    if row["ref"] == "J1" and row["layer"] == "Top":
        hand.append(("J1", "Top-side USB-C; hand solder for bottom-side-only PCBA quote", 1))
hand.sort(key=lambda row: natural_key(row[0]))
OUT.mkdir(parents=True, exist_ok=True)

groups = defaultdict(list)
for row in assembled:
    groups[(row["comment"], row["mpn"], row["footprint"], row["lcsc"])].append(row["ref"])

with (OUT / "codex_micro_wired_revA_jlc_bom.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part #"])
    for (comment, mpn, footprint, lcsc), refs in sorted(groups.items(), key=lambda item: natural_key(item[1][0])):
        writer.writerow([comment, ",".join(sorted(refs, key=natural_key)), footprint, lcsc, mpn])

with (OUT / "codex_micro_wired_revA_jlc_cpl.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for row in assembled:
        writer.writerow([
            row["ref"], f'{row["x"]:.4f}mm', f'{row["y"]:.4f}mm',
            row["layer"], f'{row["rotation"]:.2f}',
        ])

with (OUT / "codex_micro_wired_revA_hand_assembly.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["Designator", "Part / qualification note", "Qty"])
    writer.writerows(hand)

turnkey = list(assembled)
for fp in board.GetFootprints():
    ref = fp.GetReference()
    part = TURNKEY_PARTS.get(ref)
    if not part:
        continue
    pos = fp.GetPosition()
    turnkey.append({
        "ref": ref,
        "comment": part["comment"],
        "mpn": part["mpn"],
        "lcsc": part["lcsc"],
        "footprint": part["footprint"],
        "x": pcbnew.ToMM(pos.x),
        "y": pcbnew.ToMM(pos.y),
        "layer": "Bottom" if fp.IsFlipped() else "Top",
        "rotation": fp.GetOrientationDegrees() % 360,
    })
turnkey.sort(key=lambda row: natural_key(row["ref"]))

turnkey_groups = defaultdict(list)
for row in turnkey:
    turnkey_groups[(row["comment"], row["mpn"], row["footprint"], row["lcsc"])].append(row["ref"])

with (OUT / "codex_micro_wired_revA_turnkey_bom.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part #"])
    for (comment, mpn, footprint, lcsc), refs in sorted(
        turnkey_groups.items(), key=lambda item: natural_key(item[1][0])
    ):
        writer.writerow([comment, ",".join(sorted(refs, key=natural_key)), footprint, lcsc, mpn])

with (OUT / "codex_micro_wired_revA_turnkey_cpl.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for row in turnkey:
        writer.writerow([
            row["ref"], f'{row["x"]:.4f}mm', f'{row["y"]:.4f}mm',
            row["layer"], f'{row["rotation"]:.2f}',
        ])

with (OUT / "codex_micro_wired_revA_consigned_parts.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow([
        "Item", "Manufacturer Part #", "Order Qty", "Install Qty",
        "Destination", "Source", "Purpose",
    ])
    writer.writerows([
        ["Low-profile switch", "WRK-LP1", 106, "24 on 2 PCBAs", "JLCPCB consigned-parts warehouse", "https://worklouder.cc/wrk-lp1-switches", "12 switches per board plus factory spares"],
        ["Planar joystick with stock knob", "RKJXY1000006", 4, "2 on 2 PCBAs", "JLCPCB consigned-parts warehouse", "https://akizukidenshi.com/catalog/g/g114675", "In-stock electrical/mechanical sibling of RKJXY100000A"],
        ["Blank/icon keycap set", "WRK-MX-PURE", 1, "1 finished device", "JLCPCB secondary mechanical assembly", "https://worklouder.cc/wrk-mx-pure", "Fit after electrical test; one cosmetic finished unit"],
        ["Dial cap", "WRK-DIAL-2", 1, "1 finished device", "JLCPCB secondary mechanical assembly", "https://worklouder.cc/wrk-dial-2", "Fit after encoder test"],
    ])

print({
    "assembled_placements": len(assembled),
    "bom_groups": len(groups),
    "hand_assembly_lines": len(hand),
    "turnkey_placements": len(turnkey),
    "turnkey_bom_groups": len(turnkey_groups),
    "output": str(OUT),
})
