#!/usr/bin/env python3
"""Generate the Codex Keybored Rev B mechanical manufacturing package.

This is an independent CadQuery regeneration/checker for the Fusion 360 API
source in ``fusion/export_codex_micro_cnc.py``.  Both implementations use the
controlled dimensions in ``rev_b_spec.json``.  STEP is the vendor master; DXF
files are inspection and secondary-process references.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq
import ezdxf
from cadquery import exporters, importers


ROOT = Path(__file__).resolve().parents[1]
CNC = ROOT / "cnc"
STEP_DIR = CNC / "STEP"
DXF_DIR = CNC / "DXF"
STL_DIR = CNC / "STL"
VENDOR_DIR = CNC / "vendor_reference"
SPEC_PATH = CNC / "rev_b_spec.json"
SPEC = json.loads(SPEC_PATH.read_text())


def rounded_prism(width: float, depth: float, radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    """Create a filleted rectangular prism with a planar base at ``z``."""
    horizontal = cq.Workplane("XY", origin=(0, 0, z)).box(
        width - 2 * radius, depth, height, centered=(True, True, False)
    )
    vertical = cq.Workplane("XY", origin=(0, 0, z)).box(
        width, depth - 2 * radius, height, centered=(True, True, False)
    )
    result = horizontal.union(vertical)
    for x in (-width / 2 + radius, width / 2 - radius):
        for y in (-depth / 2 + radius, depth / 2 - radius):
            result = result.union(z_cylinder(x, y, radius * 2, height, z))
    return result.clean()


def z_cylinder(x: float, y: float, diameter: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY", origin=(0, 0, z)).center(x, y).circle(diameter / 2).extrude(height)


def y_cylinder(x: float, z: float, diameter: float, length: float, y0: float) -> cq.Workplane:
    solid = cq.Solid.makeCylinder(
        diameter / 2,
        length,
        cq.Vector(x, y0, z),
        cq.Vector(0, 1, 0),
    )
    return cq.Workplane("XY").newObject([solid])


def rounded_ring(outer: float, outer_radius: float, inner: float, inner_radius: float,
                 height: float, z: float = 0.0) -> cq.Workplane:
    return rounded_prism(outer, outer, outer_radius, height, z).cut(
        rounded_prism(inner, inner, inner_radius, height + 0.4, z - 0.2)
    )


def build_upper_housing() -> cq.Workplane:
    u = SPEC["upper_housing"]
    housing = rounded_ring(
        u["width"],
        u["outer_corner_radius"],
        u["inner_opening"],
        u["inner_corner_radius"],
        u["height"],
    )

    # The light guide is captured by a 0.8 mm-wide outer lip.  Its bottom face
    # sits at the same nominal level as the PCB support plane plus 0.1 mm.
    pocket_floor = u["height"] - u["lightpipe_pocket_depth"]
    pocket = rounded_ring(
        u["lightpipe_pocket_outer"],
        u["lightpipe_pocket_outer_radius"],
        u["inner_opening"],
        u["inner_corner_radius"],
        u["lightpipe_pocket_depth"] + 0.2,
        pocket_floor,
    )
    housing = housing.cut(pocket)

    pcb_radius = u["pcb_mount_pitch"] / 2
    pcb_centers = [
        (-pcb_radius, -pcb_radius),
        (-pcb_radius, pcb_radius),
        (pcb_radius, -pcb_radius),
        (pcb_radius, pcb_radius),
    ]
    for x, y in pcb_centers:
        housing = housing.union(z_cylinder(x, y, u["pcb_boss_diameter"], u["pcb_boss_height"]))
    for x, y in pcb_centers:
        housing = housing.cut(
            z_cylinder(x, y, u["pcb_pilot_diameter"], u["pcb_boss_height"] - 1.3, 1.3)
        )

    # The aluminum wedge seats on this annular flange.  Cardinal bosses are
    # reachable from the underside and intentionally use direct POM threads.
    housing = housing.union(
        z_cylinder(0, 0, 94.0, 2.5).cut(z_cylinder(0, 0, 82.0, 2.9, -0.2))
    )
    fastener_r = u["base_fastener_radius"]
    base_centers = [(-fastener_r, 0), (fastener_r, 0), (0, -fastener_r), (0, fastener_r)]
    for x, y in base_centers:
        housing = housing.union(z_cylinder(x, y, u["base_boss_diameter"], u["base_boss_height"]))
    for x, y in base_centers:
        housing = housing.cut(
            z_cylinder(x, y, u["base_pilot_diameter"], u["base_boss_height"] - 0.2, 0.0)
        )

    # Rear USB-C cable opening.  A horizontal capsule gives cutter-friendly
    # R2.3 ends and opens through the top edge instead of trapping the plug.
    usb_r = u["usb_notch_height"] / 2
    usb_half_centers = (u["usb_notch_width"] - u["usb_notch_height"]) / 2
    usb_box = (
        cq.Workplane("XY", origin=(0, 0, u["usb_notch_center_z"] - usb_r))
        .box(usb_half_centers * 2, 20.0, u["usb_notch_height"], centered=(True, True, False))
        .translate((0, 50, 0))
    )
    usb_cut = usb_box
    for x in (-usb_half_centers, usb_half_centers):
        usb_cut = usb_cut.union(y_cylinder(x, u["usb_notch_center_z"], u["usb_notch_height"], 20.0, 40.0))
    housing = housing.cut(usb_cut)

    # Reserved for a future Bluetooth pairing/reset actuator.  The wired PCB
    # does not depend on it, so the same enclosure accepts either PCB revision.
    housing = housing.cut(
        y_cylinder(
            u["service_hole_x"],
            u["service_hole_z"],
            u["service_hole_diameter"],
            20.0,
            40.0,
        )
    )
    return housing.clean()


def underside_z(y: float) -> float:
    b = SPEC["bottom_weight"]
    center_t = (b["front_thickness"] + b["rear_thickness"]) / 2
    return b["rear_thickness"] - center_t - y * math.tan(math.radians(b["tilt_degrees"]))


def build_bottom_weight(with_engraving: bool = True) -> cq.Workplane:
    b = SPEC["bottom_weight"]
    r = b["diameter"] / 2
    cylinder = z_cylinder(0, 0, b["diameter"], b["rear_thickness"])

    # Side trapezoid extruded through X, intersected with the cylindrical blank.
    span = 65.0
    side = (
        cq.Workplane("YZ")
        .polyline([
            (-span, underside_z(-span)),
            (span, underside_z(span)),
            (span, b["rear_thickness"]),
            (-span, b["rear_thickness"]),
        ])
        .close()
        .extrude(r + 20.0, both=True)
    )
    weight = cylinder.intersect(side)

    fastener_r = SPEC["upper_housing"]["base_fastener_radius"]
    centers = [(-fastener_r, 0), (fastener_r, 0), (0, -fastener_r), (0, fastener_r)]
    for x, y in centers:
        weight = weight.cut(z_cylinder(x, y, b["fastener_clearance_diameter"], 16.0, -2.0))
        local_z = underside_z(y)
        weight = weight.cut(
            z_cylinder(
                x,
                y,
                b["counterbore_diameter"],
                b["counterbore_depth"] + 0.2,
                local_z - 0.2,
            )
        )

    # Capture a purchased JIS G-65 O-ring in the desk-facing plane.  The
    # 3.6 mm-wide, 2.2 mm-deep groove leaves 0.9 mm nominal rubber protrusion
    # and remains 2.95 mm clear of the four screw counterbores.
    theta = math.radians(b["tilt_degrees"])
    desk_plane = cq.Plane(
        origin=(0, 0, underside_z(0)),
        xDir=(-1, 0, 0),
        normal=(0, -math.sin(theta), -math.cos(theta)),
    )
    groove_outer = b["oring_groove_center_diameter"] + b["oring_groove_width"]
    groove_inner = b["oring_groove_center_diameter"] - b["oring_groove_width"]
    groove = (
        cq.Workplane(desk_plane)
        .circle(groove_outer / 2)
        .circle(groove_inner / 2)
        .extrude(-b["oring_groove_depth"])
    )
    weight = weight.cut(groove)

    if with_engraving:
        # Negative depth from this outward-facing plane cuts into aluminum.
        plane = desk_plane
        logo = (
            cq.Workplane(plane)
            .center(0, 4.0)
            .text(
                "CODEX KEYBORED",
                4.2,
                -b["engraving_depth"],
                font="Arial",
                kind="bold",
                halign="center",
                valign="center",
                combine=False,
            )
        )
        strapline = (
            cq.Workplane(plane)
            .center(0, -4.0)
            .text(
                "ABSOLUTELY VIBE-CODED",
                2.1,
                -b["engraving_depth"],
                font="Arial",
                kind="regular",
                halign="center",
                valign="center",
                combine=False,
            )
        )
        weight = weight.cut(logo).cut(strapline)
    return weight.clean()


def build_lightpipe() -> cq.Workplane:
    p = SPEC["lightpipe"]
    guide = rounded_ring(
        p["outer"],
        p["outer_corner_radius"],
        p["inner"],
        p["inner_corner_radius"],
        p["thickness"],
    )
    # Match the open-top USB notch so the cable never loads the PMMA edge.
    gap = cq.Workplane("XY", origin=(0, 0, -0.2)).box(
        p["rear_usb_gap"], 20.0, p["thickness"] + 0.4, centered=(True, True, False)
    ).translate((0, 50.0, 0))
    return guide.cut(gap).clean()


def build_joystick_cap() -> cq.Workplane:
    j = SPEC["joystick_cap"]
    cap = z_cylinder(0, 0, j["diameter"], j["height"])
    return cap.cut(z_cylinder(0, 0, j["shaft_pilot_diameter"], j["shaft_pilot_depth"])).clean()


def build_purchased_oring_reference() -> cq.Workplane:
    """Model the purchased G-65 ring for fit checking, not CNC quotation."""
    ring = SPEC["anti_slip_ring"]
    major_radius = (ring["inner_diameter"] + ring["cross_section_diameter"]) / 2
    minor_radius = ring["cross_section_diameter"] / 2
    solid = cq.Solid.makeTorus(major_radius, minor_radius)
    return cq.Workplane("XY").newObject([solid])


def add_rounded_rectangle(msp, width: float, depth: float, radius: float, layer: str) -> None:
    x = width / 2
    y = depth / 2
    r = radius
    pts = [(-x + r, -y), (x - r, -y), (x, -y + r), (x, y - r),
           (x - r, y), (-x + r, y), (-x, y - r), (-x, -y + r)]
    for a, b in ((0, 1), (2, 3), (4, 5), (6, 7)):
        msp.add_line(pts[a], pts[b], dxfattribs={"layer": layer})
    centers = [(x - r, -y + r), (x - r, y - r), (-x + r, y - r), (-x + r, -y + r)]
    angles = [(270, 360), (0, 90), (90, 180), (180, 270)]
    for center, (start, end) in zip(centers, angles):
        msp.add_arc(center, r, start, end, dxfattribs={"layer": layer})


def export_reference_dxf() -> None:
    pcb = SPEC["pcb"]
    u = SPEC["upper_housing"]
    fastener_r = u["base_fastener_radius"]

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    add_rounded_rectangle(msp, u["width"], u["depth"], u["outer_corner_radius"], "OUTLINE")
    add_rounded_rectangle(msp, u["inner_opening"], u["inner_opening"], u["inner_corner_radius"], "OPENING")
    for x in (-pcb["mount_pitch"] / 2, pcb["mount_pitch"] / 2):
        for y in (-pcb["mount_pitch"] / 2, pcb["mount_pitch"] / 2):
            msp.add_circle((x, y), u["pcb_pilot_diameter"] / 2, dxfattribs={"layer": "M3_TAP"})
    doc.saveas(DXF_DIR / "CM2-001_upper_housing_top_profile.dxf")

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_circle((0, 0), SPEC["bottom_weight"]["diameter"] / 2, dxfattribs={"layer": "OUTLINE"})
    for x, y in [(-fastener_r, 0), (fastener_r, 0), (0, -fastener_r), (0, fastener_r)]:
        msp.add_circle((x, y), SPEC["bottom_weight"]["fastener_clearance_diameter"] / 2,
                       dxfattribs={"layer": "M2P5_CLEARANCE"})
        msp.add_circle((x, y), SPEC["bottom_weight"]["counterbore_diameter"] / 2,
                       dxfattribs={"layer": "COUNTERBORE"})
    groove_center = SPEC["bottom_weight"]["oring_groove_center_diameter"]
    groove_width = SPEC["bottom_weight"]["oring_groove_width"]
    msp.add_circle((0, 0), (groove_center + groove_width) / 2,
                   dxfattribs={"layer": "G65_ORING_GROOVE_OUTER"})
    msp.add_circle((0, 0), (groove_center - groove_width) / 2,
                   dxfattribs={"layer": "G65_ORING_GROOVE_INNER"})
    doc.saveas(DXF_DIR / "CM2-002_bottom_weight_profile.dxf")

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    add_rounded_rectangle(msp, pcb["width"], pcb["depth"], pcb["corner_radius"], "EDGE_CUTS")
    for x in (-pcb["mount_pitch"] / 2, pcb["mount_pitch"] / 2):
        for y in (-pcb["mount_pitch"] / 2, pcb["mount_pitch"] / 2):
            msp.add_circle((x, y), pcb["mount_hole_diameter"] / 2, dxfattribs={"layer": "NPTH"})
    doc.saveas(DXF_DIR / "CM2-006_top_pcb_outline.dxf")


def bbox(shape: cq.Workplane) -> list[float]:
    b = shape.val().BoundingBox()
    return [round(b.xlen, 3), round(b.ylen, 3), round(b.zlen, 3)]


def export_shape(shape: cq.Workplane, stem: str, stl: bool = False) -> dict:
    step_path = STEP_DIR / f"{stem}.step"
    exporters.export(shape, str(step_path), exportType="STEP")
    if stl:
        exporters.export(shape, str(STL_DIR / f"{stem}.stl"), tolerance=0.03, angularTolerance=0.12)
    imported = importers.importStep(str(step_path))
    return {
        "file": step_path.name,
        "bbox_mm": bbox(imported),
        "volume_mm3": round(imported.val().Volume(), 2),
        "solids": len(imported.solids().vals()),
    }


def main() -> None:
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    DXF_DIR.mkdir(parents=True, exist_ok=True)
    STL_DIR.mkdir(parents=True, exist_ok=True)
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)

    parts = {
        "CM2-001_upper_housing": build_upper_housing(),
        "CM2-002_bottom_weight": build_bottom_weight(),
        "CM2-003_lightpipe": build_lightpipe(),
        "CM2-004_joystick_cap": build_joystick_cap(),
    }
    results = [export_shape(shape, name) for name, shape in parts.items()]
    purchased_ring = build_purchased_oring_reference()
    ring_path = VENDOR_DIR / "JLCMC_AMFG-P5-A65-65_G65_oring.step"
    exporters.export(purchased_ring, str(ring_path), exportType="STEP")
    export_reference_dxf()

    manifest = {
        "revision": SPEC["revision"],
        "generator": "CadQuery 2.5.2 independent regeneration",
        "source_spec": str(SPEC_PATH.relative_to(ROOT)),
        "parts": results,
        "purchased_reference": {
            "file": str(ring_path.relative_to(ROOT)),
            "supplier_part_number": SPEC["anti_slip_ring"]["part_number"],
            "bbox_mm": bbox(purchased_ring),
            "volume_mm3": round(purchased_ring.val().Volume(), 2),
            "manufacturing_route": "Purchase from JLCMC; do not upload as a CNC part",
        },
    }
    (CNC / "rev_b_geometry_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
