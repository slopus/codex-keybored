#!/usr/bin/env python3
"""Build the complete Rev A2 order handoff with a deterministic manifest."""

from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output" / "CODEX_KEYBORED_RevA2_order_handoff.zip"
FIXED_TIME = (2026, 7, 17, 12, 0, 0)

PATTERNS = (
    "README.md",
    "mechanical-bom.md",
    "firmware-and-compliance-notes.md",
    "fusion/Codex_Micro_RevA.f3d",
    "fusion/*.py",
    "cnc/STEP/*.step",
    "cnc/DXF/*.dxf",
    "cnc/drawings/*.pdf",
    "electronics/README.md",
    "electronics/kicad/codex_micro_wired_revA.kicad_pcb",
    "electronics/kicad/codex_micro_wired_revA.kicad_pro",
    "electronics/production/**/*",
    "firmware/factory_key_test.html",
    "firmware/stm32/README.md",
    "firmware/stm32/CMakeLists.txt",
    "firmware/stm32/fetch_dependencies.sh",
    "firmware/stm32/*.c",
    "firmware/stm32/*.h",
    "firmware/stm32/board/**/*",
    "firmware/stm32/release/*",
    "output/pdf/*.pdf",
    "scripts/build_complete_handoff.py",
)


def zip_info(name: str) -> ZipInfo:
    info = ZipInfo(name, FIXED_TIME)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


files: dict[str, Path] = {}
for pattern in PATTERNS:
    for path in ROOT.glob(pattern):
        if path.is_file() and path.name not in {".DS_Store"}:
            files[path.relative_to(ROOT).as_posix()] = path

manifest_lines = []
for name, path in sorted(files.items()):
    data = path.read_bytes()
    manifest_lines.append(f"{hashlib.sha256(data).hexdigest()}  {len(data):>10}  {name}")

manifest = (
    "CODEX KEYBORED Rev A2 - Complete Order Handoff\n"
    "SHA-256 checksums and uncompressed byte counts\n\n"
    + "\n".join(manifest_lines)
    + "\n"
).encode()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
    archive.writestr(zip_info("MANIFEST-SHA256.txt"), manifest)
    for name, path in sorted(files.items()):
        archive.writestr(zip_info(name), path.read_bytes())

print(
    {
        "output": str(OUTPUT),
        "files": len(files) + 1,
        "bytes": OUTPUT.stat().st_size,
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    }
)
