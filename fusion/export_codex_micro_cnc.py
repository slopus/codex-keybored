"""Create and export the vendor-neutral Codex Micro CNC package from Fusion 360.

The active user document is never saved or closed.  Each production part is built
in a temporary Fusion Design document, exported as STEP/DXF, and the temporary
document is closed without saving.  The script finally re-activates the original
document.
"""

import json
import math
import os

import adsk.core
import adsk.fusion


EXPORT_ROOT = "/Users/steve/Documents/CodexKB/codex-micro/cnc"

# The official side views show that the circular aluminium base is a wedge,
# not a flat puck.  The top mounting face remains normal to the keyboard's
# fasteners; the lower face sets the assembled keyboard at this desk angle.
BOTTOM_DIAMETER_MM = 94.0
BOTTOM_TILT_DEG = 5.0
BOTTOM_FRONT_THICKNESS_MM = 3.8
BOTTOM_REAR_THICKNESS_MM = 12.0


def _cm(mm):
    return mm / 10.0


def _p(x_mm, y_mm, z_mm=0.0):
    return adsk.core.Point3D.create(_cm(x_mm), _cm(y_mm), _cm(z_mm))


def _rounded_rectangle(sketch, cx, cy, width, height, radius):
    x0 = cx - width / 2.0
    x1 = cx + width / 2.0
    y0 = cy - height / 2.0
    y1 = cy + height / 2.0
    r = min(radius, width / 2.0, height / 2.0)
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    lines.addByTwoPoints(_p(x0 + r, y0), _p(x1 - r, y0))
    arcs.addByCenterStartSweep(_p(x1 - r, y0 + r), _p(x1 - r, y0), math.pi / 2)
    lines.addByTwoPoints(_p(x1, y0 + r), _p(x1, y1 - r))
    arcs.addByCenterStartSweep(_p(x1 - r, y1 - r), _p(x1, y1 - r), math.pi / 2)
    lines.addByTwoPoints(_p(x1 - r, y1), _p(x0 + r, y1))
    arcs.addByCenterStartSweep(_p(x0 + r, y1 - r), _p(x0 + r, y1), math.pi / 2)
    lines.addByTwoPoints(_p(x0, y1 - r), _p(x0, y0 + r))
    arcs.addByCenterStartSweep(_p(x0 + r, y0 + r), _p(x0, y0 + r), math.pi / 2)


def _extrude(component, profile_or_profiles, height_mm, operation, symmetric=False):
    extrudes = component.features.extrudeFeatures
    inp = extrudes.createInput(profile_or_profiles, operation)
    distance = adsk.core.ValueInput.createByReal(_cm(height_mm))
    if symmetric:
        inp.setSymmetricExtent(distance, True)
    else:
        inp.setDistanceExtent(False, distance)
    return extrudes.add(inp)


def _move(component, bodies, z_mm):
    entities = adsk.core.ObjectCollection.create()
    for body in bodies:
        entities.add(body)
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(0, 0, _cm(z_mm))
    inp = component.features.moveFeatures.createInput2(entities)
    inp.defineAsFreeMove(transform)
    component.features.moveFeatures.add(inp)


def _new_rounded_box(component, name, width, depth, height, radius, z=0.0):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = name + "_OUTLINE"
    _rounded_rectangle(sketch, 0, 0, width, depth, radius)
    feature = _extrude(
        component,
        sketch.profiles.item(0),
        height,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    if z:
        _move(component, [body], z)
    return body


def _new_cylinder(component, name, x, y, diameter, height, z=0.0):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = name + "_PROFILE"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(_p(x, y), _cm(diameter / 2.0))
    feature = _extrude(
        component,
        sketch.profiles.item(0),
        height,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    if z:
        _move(component, [body], z)
    return body


def _new_ring(component, name, outer_d, inner_d, height, z=0.0):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = name + "_PROFILE"
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(_p(0, 0), _cm(outer_d / 2.0))
    circles.addByCenterRadius(_p(0, 0), _cm(inner_d / 2.0))
    annulus = None
    for i in range(sketch.profiles.count):
        candidate = sketch.profiles.item(i)
        if candidate.profileLoops.count == 2:
            annulus = candidate
            break
    feature = _extrude(
        component,
        annulus,
        height,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    if z:
        _move(component, [body], z)
    return body


def _combine(component, target, tools, operation):
    collection = adsk.core.ObjectCollection.create()
    for body in tools:
        collection.add(body)
    inp = component.features.combineFeatures.createInput(target, collection)
    inp.operation = operation
    inp.isKeepToolBodies = False
    return component.features.combineFeatures.add(inp)


def _cut_below_sloped_plane(component, target, top_z_mm, front_thickness_mm,
                            rear_thickness_mm, tilt_deg):
    """Cut below the wedge's lower plane while retaining a flat top face.

    Front is -Y (the 2U-key edge) and rear is +Y (USB edge).  The temporary
    oriented box has its upper face coincident with the wanted lower plane.
    """
    manager = adsk.fusion.TemporaryBRepManager.get()
    angle = math.radians(tilt_deg)
    x_axis = adsk.core.Vector3D.create(1.0, 0.0, 0.0)
    along_plane = adsk.core.Vector3D.create(0.0, math.cos(angle), -math.sin(angle))
    normal = adsk.core.Vector3D.create(0.0, math.sin(angle), math.cos(angle))

    center_thickness = (front_thickness_mm + rear_thickness_mm) / 2.0
    plane_z = top_z_mm - center_thickness
    cutter_height_mm = 60.0
    cutter_center = _p(
        0.0,
        -normal.y * cutter_height_mm / 2.0,
        plane_z - normal.z * cutter_height_mm / 2.0,
    )
    box = adsk.core.OrientedBoundingBox3D.create(
        cutter_center,
        x_axis,
        along_plane,
        _cm(130.0),
        _cm(150.0),
        _cm(cutter_height_mm),
    )
    cutter = component.bRepBodies.add(manager.createBox(box))
    _combine(
        component,
        target,
        [cutter],
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )


def _wedge_bottom_z(y_mm):
    """Local Z of the sloped underside in the exported part coordinates."""
    top_z = BOTTOM_REAR_THICKNESS_MM
    center_thickness = (
        BOTTOM_FRONT_THICKNESS_MM + BOTTOM_REAR_THICKNESS_MM
    ) / 2.0
    return top_z - center_thickness - y_mm * math.tan(math.radians(BOTTOM_TILT_DEG))


def _cut_rounded_xy(component, target, width, depth, radius, height):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = "INNER_CAVITY_PROFILE"
    _rounded_rectangle(sketch, 0, 0, width, depth, radius)
    return _extrude(
        component,
        sketch.profiles.item(0),
        height,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )


def _cut_side_ports(component, target):
    """Cut rear-facing ports with transient BReps, independent of sketch axes."""
    manager = adsk.fusion.TemporaryBRepManager.get()
    x_axis = adsk.core.Vector3D.create(1, 0, 0)
    y_axis = adsk.core.Vector3D.create(0, 1, 0)

    # USB-C capsule: 10.2 x 4.6 mm, R2.3, swept 20 mm through rear wall.
    usb_tools = []
    box = adsk.core.OrientedBoundingBox3D.create(
        _p(0, 50, 3.2), x_axis, y_axis, _cm(5.6), _cm(20.0), _cm(4.6)
    )
    usb_tools.append(component.bRepBodies.add(manager.createBox(box)))
    for x in (-2.8, 2.8):
        cylinder = manager.createCylinderOrCone(
            _p(x, 40, 3.2), _cm(2.3), _p(x, 60, 3.2), _cm(2.3)
        )
        usb_tools.append(component.bRepBodies.add(cylinder))

    button = manager.createCylinderOrCone(
        _p(14.0, 40, 5.0), _cm(2.1), _p(14.0, 60, 5.0), _cm(2.1)
    )
    usb_tools.append(component.bRepBodies.add(button))
    _combine(component, target, usb_tools, adsk.fusion.FeatureOperations.CutFeatureOperation)


def _cut_cylinders(component, target, centers, diameter, height, z=0.0, name="CUT"):
    tools = []
    for i, (x, y) in enumerate(centers, 1):
        tools.append(_new_cylinder(component, f"{name}_{i}", x, y, diameter, height, z))
    _combine(component, target, tools, adsk.fusion.FeatureOperations.CutFeatureOperation)


def _build_upper_housing(root):
    outer = _new_rounded_box(root, "CM2_001_UPPER_HOUSING", 108.0, 108.0, 10.3, 14.0)
    _cut_rounded_xy(root, outer, 92.0, 92.0, 7.0, 10.3)

    flange = _new_ring(root, "BOTTOM_DISC_SUPPORT_FLANGE", 94.0, 82.0, 2.5)
    boss_centers = [(-39.0, -39.0), (-39.0, 39.0), (39.0, -39.0), (39.0, 39.0)]
    bosses = [
        _new_cylinder(root, f"TOP_PCB_BOSS_{i}", x, y, 16.0, 8.3)
        for i, (x, y) in enumerate(boss_centers, 1)
    ]
    bottom_centers = [(-43.5, 0), (43.5, 0), (0, -43.5), (0, 43.5)]
    bottom_bosses = [
        _new_cylinder(root, f"BOTTOM_FASTENER_BOSS_{i}", x, y, 8.0, 6.0)
        for i, (x, y) in enumerate(bottom_centers, 1)
    ]
    _combine(
        root,
        outer,
        [flange] + bosses + bottom_bosses,
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
    )

    # M3 insert pilot: 4.0 mm diameter, 7.0 mm deep, 1.3 mm floor.
    _cut_cylinders(root, outer, boss_centers, 4.0, 7.0, 1.3, "M3_INSERT_PILOT")
    # M2.5 thread-forming screw pilot in 6 mm integrated attachment bosses.
    _cut_cylinders(root, outer, bottom_centers, 2.1, 5.8, 0.0, "M2P5_PILOT")
    _cut_side_ports(root, outer)
    return outer


def _build_bottom_weight(root):
    # Start with the maximum rear thickness, then remove everything below the
    # 5-degree desk plane.  This yields a constant flat mounting face at Z=12.
    disc = _new_cylinder(
        root,
        "CM2_002_BOTTOM_WEIGHT_WEDGE_5DEG",
        0,
        0,
        BOTTOM_DIAMETER_MM,
        BOTTOM_REAR_THICKNESS_MM,
    )
    _cut_below_sloped_plane(
        root,
        disc,
        BOTTOM_REAR_THICKNESS_MM,
        BOTTOM_FRONT_THICKNESS_MM,
        BOTTOM_REAR_THICKNESS_MM,
        BOTTOM_TILT_DEG,
    )

    centers = [(-43.5, 0), (43.5, 0), (0, -43.5), (0, 43.5)]
    # The screw axes stay perpendicular to the keyboard/top mounting face.
    # Each counterbore starts at its local point on the sloped underside.
    clearance_tools = []
    counterbore_tools = []
    for index, (x_mm, y_mm) in enumerate(centers, 1):
        underside_z = _wedge_bottom_z(y_mm)
        clearance_tools.append(_new_cylinder(
            root,
            f"M2P5_CLEARANCE_{index}",
            x_mm,
            y_mm,
            2.8,
            BOTTOM_REAR_THICKNESS_MM - underside_z + 0.8,
            underside_z - 0.4,
        ))
        counterbore_tools.append(_new_cylinder(
            root,
            f"M2P5_HEAD_COUNTERBORE_{index}",
            x_mm,
            y_mm,
            5.0,
            1.9,
            underside_z - 0.2,
        ))
    _combine(
        root,
        disc,
        clearance_tools + counterbore_tools,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )
    return disc


def _build_lightpipe(root):
    outer = _new_rounded_box(root, "CM2_003_OPTIONAL_LIGHTPIPE", 108.0, 108.0, 1.5, 14.0)
    _cut_rounded_xy(root, outer, 92.0, 92.0, 7.0, 1.5)
    return outer


def _build_joystick_cap(root):
    cap = _new_cylinder(root, "CM2_004_JOYSTICK_CAP", 0, 0, 14.5, 7.0)
    _cut_cylinders(root, cap, [(0, 0)], 2.1, 5.5, 0.0, "SHAFT_PILOT")
    return cap


def _save_outline_dxf(root, filename, kind):
    sketch = root.sketches.add(root.xYConstructionPlane)
    if kind == "upper":
        _rounded_rectangle(sketch, 0, 0, 108.0, 108.0, 14.0)
        _rounded_rectangle(sketch, 0, 0, 92.0, 92.0, 7.0)
        for x, y in [(-39, -39), (-39, 39), (39, -39), (39, 39)]:
            sketch.sketchCurves.sketchCircles.addByCenterRadius(_p(x, y), _cm(2.0))
    elif kind == "bottom":
        sketch.sketchCurves.sketchCircles.addByCenterRadius(_p(0, 0), _cm(47.0))
        for x, y in [(-43.5, 0), (43.5, 0), (0, -43.5), (0, 43.5)]:
            sketch.sketchCurves.sketchCircles.addByCenterRadius(_p(x, y), _cm(1.4))
    elif kind == "rubber":
        sketch.sketchCurves.sketchCircles.addByCenterRadius(_p(0, 0), _cm(46.0))
        sketch.sketchCurves.sketchCircles.addByCenterRadius(_p(0, 0), _cm(41.0))
    elif kind == "top_pcb":
        _rounded_rectangle(sketch, 0, 0, 90.0, 90.0, 5.0)
        for x, y in [(-39, -39), (-39, 39), (39, -39), (39, 39)]:
            sketch.sketchCurves.sketchCircles.addByCenterRadius(_p(x, y), _cm(1.6))
    if not sketch.saveAsDXF(filename):
        raise RuntimeError("DXF export failed: " + filename)


def _export_part(app, original_doc, name, builder, step_name, dxf_name=None, dxf_kind=None):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = name
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
        root = design.rootComponent
        body = builder(root)
        if body:
            body.name = name

        step_path = os.path.join(EXPORT_ROOT, "STEP", step_name)
        options = design.exportManager.createSTEPExportOptions(step_path, root)
        if not design.exportManager.execute(options):
            raise RuntimeError("STEP export failed: " + step_path)

        if dxf_name:
            dxf_path = os.path.join(EXPORT_ROOT, "DXF", dxf_name)
            _save_outline_dxf(root, dxf_path, dxf_kind)
        result = {"name": name, "step": step_path, "dxf": dxf_name}
    finally:
        original_doc.activate()
        doc.close(False)
    return result


def _export_reference_dxf(app, original_doc, name, dxf_name, kind):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = name
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
        root = design.rootComponent
        path = os.path.join(EXPORT_ROOT, "DXF", dxf_name)
        _save_outline_dxf(root, path, kind)
    finally:
        original_doc.activate()
        doc.close(False)
    return path


def run(_context: str):
    app = adsk.core.Application.get()
    original_doc = app.activeDocument
    os.makedirs(os.path.join(EXPORT_ROOT, "STEP"), exist_ok=True)
    os.makedirs(os.path.join(EXPORT_ROOT, "DXF"), exist_ok=True)

    results = []
    try:
        results.append(_export_part(
            app,
            original_doc,
            "CM2-001 Upper Housing",
            _build_upper_housing,
            "CM2-001_upper_housing.step",
            "CM2-001_upper_housing_top_profile.dxf",
            "upper",
        ))
        results.append(_export_part(
            app,
            original_doc,
            "CM2-002 Bottom Weight",
            _build_bottom_weight,
            "CM2-002_bottom_weight.step",
            "CM2-002_bottom_weight_profile.dxf",
            "bottom",
        ))
        results.append(_export_part(
            app,
            original_doc,
            "CM2-003 Optional Lightpipe",
            _build_lightpipe,
            "CM2-003_optional_lightpipe.step",
        ))
        results.append(_export_part(
            app,
            original_doc,
            "CM2-004 Joystick Cap",
            _build_joystick_cap,
            "CM2-004_joystick_cap.step",
        ))
        _export_reference_dxf(
            app,
            original_doc,
            "CM2 Anti-slip Ring",
            "CM2-005_anti_slip_ring_profile.dxf",
            "rubber",
        )
        _export_reference_dxf(
            app,
            original_doc,
            "CM2 Top PCB Outline",
            "CM2-006_top_pcb_outline.dxf",
            "top_pcb",
        )
    finally:
        original_doc.activate()

    print(json.dumps({
        "status": "CNC package exported; source Fusion document not saved",
        "export_root": EXPORT_ROOT,
        "parts": results,
        "active_document": app.activeDocument.name,
    }))
