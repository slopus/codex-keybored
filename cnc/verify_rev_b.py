#!/usr/bin/env python3
"""Verify Rev B STEP round trips and all controlled mechanical interfaces."""

from __future__ import annotations

import json
from pathlib import Path

from cadquery import importers


ROOT = Path(__file__).resolve().parents[1]
CNC = ROOT / "cnc"
STEP = CNC / "STEP"
SPEC = json.loads((CNC / "rev_b_spec.json").read_text())


EXPECTED = {
    "CM2-001_upper_housing.step": (108.0, 108.0, 10.3),
    "CM2-002_bottom_weight.step": (94.0, 94.0, 12.0),
    "CM2-003_lightpipe.step": (106.1, 106.1, 1.5),
    "CM2-004_joystick_cap.step": (14.5, 14.5, 7.0),
}


def close(actual: float, expected: float, tolerance: float = 0.01) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> None:
    parts = []
    for filename, expected in EXPECTED.items():
        path = STEP / filename
        assert path.exists(), path
        shape = importers.importStep(str(path))
        solids = shape.solids().vals()
        assert len(solids) == 1, f"{filename}: expected one solid, got {len(solids)}"
        bounds = shape.val().BoundingBox()
        actual = (bounds.xlen, bounds.ylen, bounds.zlen)
        assert all(close(a, e) for a, e in zip(actual, expected)), (filename, actual, expected)
        parts.append({
            "file": filename,
            "solid": True,
            "bbox_mm": [round(v, 3) for v in actual],
            "volume_mm3": round(shape.val().Volume(), 2),
        })

    pcb = SPEC["pcb"]
    upper = SPEC["upper_housing"]
    bottom = SPEC["bottom_weight"]
    guide = SPEC["lightpipe"]
    ring = SPEC["anti_slip_ring"]

    checks = {
        "pcb_per_side_clearance_mm": (upper["inner_opening"] - pcb["width"]) / 2,
        "pcb_mount_pitch_error_mm": abs(upper["pcb_mount_pitch"] - pcb["mount_pitch"]),
        "lightpipe_outer_per_side_clearance_mm": (
            upper["lightpipe_pocket_outer"] - guide["outer"]
        ) / 2,
        "lightpipe_overhang_into_opening_mm": (
            upper["inner_opening"] - guide["inner"]
        ) / 2,
        "lightpipe_to_pcb_per_side_clearance_mm": (guide["inner"] - pcb["width"]) / 2,
        "usb_notch_shell_total_clearance_mm": upper["usb_notch_width"] - pcb["usb_shell_width"],
        "oring_groove_edge_margin_mm": (
            bottom["diameter"] / 2
            - (bottom["oring_groove_center_diameter"] + bottom["oring_groove_width"]) / 2
        ),
        "oring_groove_to_counterbore_margin_mm": (
            upper["base_fastener_radius"]
            - bottom["counterbore_diameter"] / 2
            - (bottom["oring_groove_center_diameter"] + bottom["oring_groove_width"]) / 2
        ),
        "oring_nominal_side_clearance_mm": (
            bottom["oring_groove_width"] - ring["cross_section_diameter"]
        ) / 2,
        "oring_nominal_protrusion_mm": (
            ring["cross_section_diameter"] - bottom["oring_groove_depth"]
        ),
        "minimum_front_material_below_groove_mm": (
            bottom["front_thickness"] - bottom["oring_groove_depth"]
        ),
        "base_counterbore_edge_margin_mm": (
            bottom["diameter"] / 2
            - upper["base_fastener_radius"]
            - bottom["counterbore_diameter"] / 2
        ),
    }

    assert checks["pcb_per_side_clearance_mm"] >= 0.8
    assert close(checks["pcb_mount_pitch_error_mm"], 0.0)
    assert checks["lightpipe_outer_per_side_clearance_mm"] >= 0.10
    assert checks["lightpipe_to_pcb_per_side_clearance_mm"] >= 0.50
    assert checks["usb_notch_shell_total_clearance_mm"] >= 1.5
    assert checks["oring_groove_edge_margin_mm"] >= 10.0
    assert checks["oring_groove_to_counterbore_margin_mm"] >= 2.5
    assert checks["oring_nominal_side_clearance_mm"] >= 0.20
    assert 0.75 <= checks["oring_nominal_protrusion_mm"] <= 1.10
    assert checks["minimum_front_material_below_groove_mm"] >= 1.5
    assert checks["base_counterbore_edge_margin_mm"] >= 3.0

    volumes = {item["file"]: item["volume_mm3"] for item in parts}
    mass = {
        "upper_black_pom_g": round(volumes["CM2-001_upper_housing.step"] * 0.00141, 1),
        "bottom_6061_g": round(volumes["CM2-002_bottom_weight.step"] * 0.00270, 1),
        "lightpipe_pmma_g": round(volumes["CM2-003_lightpipe.step"] * 0.00118, 1),
        "joystick_cap_pom_g": round(volumes["CM2-004_joystick_cap.step"] * 0.00141, 1),
        "purchased_g65_nbr_oring_g": 1.9,
    }
    mass["mechanical_total_g"] = round(sum(mass.values()), 1)

    report = {
        "revision": "B",
        "status": "PASS",
        "parts": parts,
        "interface_checks": {key: round(value, 3) for key, value in checks.items()},
        "estimated_mass": mass,
        "notes": [
            "PCB outline checked against generated KiCad source: 90 x 90 mm, R4, 78 mm mount pitch.",
            "PCB coordinate mapping is rotated 180 degrees in the assembly: USB at board Y=5.1 maps to rear +Y.",
            "A single purchased JLCMC AMFG-P5-A65-65 G-65 O-ring replaces both the rejected TPU ring and temporary discrete-foot options.",
            "JIS G-65 envelope: 64.4 mm nominal ID x 3.1 mm section; black NBR 65A.",
            "The O-ring is captured without adhesive in a 67.5 mm centerline diameter x 3.6 mm wide x 2.2 mm deep groove.",
            "First-article physical fit inspection remains mandatory before ordering multiples.",
        ],
    }
    (CNC / "rev_b_fit_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
