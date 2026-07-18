#!/usr/bin/env python3
"""Build deterministic CODEX KEYBORED Rev B factory handoff archives."""

from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent.parent
FIXED_TIME = (2026, 7, 17, 12, 0, 0)

COMMON_MECHANICAL = (
    "README.md",
    "mechanical-bom.md",
    "cnc/REV_B_FACTORY_README.md",
    "cnc/rev_b_spec.json",
    "cnc/rev_b_geometry_manifest.json",
    "cnc/rev_b_fit_report.json",
    "cnc/STEP/*.step",
    "cnc/DXF/*.dxf",
    "cnc/drawings/*.pdf",
    "cnc/vendor_reference/*.step",
    "cnc/generate_rev_b_step.py",
    "cnc/verify_rev_b.py",
    "fusion/*.py",
)

COMPLETE_PATTERNS = COMMON_MECHANICAL + (
    "firmware-and-compliance-notes.md",
    "fusion/Codex_Micro_RevA.f3d",
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
    "docs/index.html",
    "docs/assets/renders/revb-jlcmc-g65-oring.png",
    "docs/assets/screenshots/jlccnc-revb-base-g65-quote.png",
    "docs/assets/screenshots/jlcmc-g65-ring-cart.png",
    "output/pdf/*.pdf",
    "scripts/build_complete_handoff.py",
)

PACKAGES = {
    "CODEX_KEYBORED_RevB_mechanical_factory_handoff.zip": (
        "CODEX KEYBORED Mechanics Rev B - Factory Handoff",
        COMMON_MECHANICAL,
    ),
    "CODEX_KEYBORED_RevB_order_handoff.zip": (
        "CODEX KEYBORED Mechanics Rev B + Electronics Rev A2 - Complete Order Handoff",
        COMPLETE_PATTERNS,
    ),
}


def zip_info(name: str) -> ZipInfo:
    info = ZipInfo(name, FIXED_TIME)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def collect_files(patterns: tuple[str, ...]) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_file() and path.name != ".DS_Store":
                files[path.relative_to(ROOT).as_posix()] = path
    return files


def build_archive(filename: str, title: str, patterns: tuple[str, ...]) -> dict[str, object]:
    files = collect_files(patterns)
    manifest_lines = []
    for name, path in sorted(files.items()):
        data = path.read_bytes()
        manifest_lines.append(f"{hashlib.sha256(data).hexdigest()}  {len(data):>10}  {name}")

    manifest = (
        f"{title}\n"
        "SHA-256 checksums and uncompressed byte counts\n\n"
        + "\n".join(manifest_lines)
        + "\n"
    ).encode()

    output = ROOT / "output" / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(zip_info("MANIFEST-SHA256.txt"), manifest)
        for name, path in sorted(files.items()):
            archive.writestr(zip_info(name), path.read_bytes())

    return {
        "output": str(output),
        "files": len(files) + 1,
        "bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


for package_name, (package_title, package_patterns) in PACKAGES.items():
    print(build_archive(package_name, package_title, package_patterns))
