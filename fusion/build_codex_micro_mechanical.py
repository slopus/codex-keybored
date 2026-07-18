"""Build a parameterized Codex Micro mechanical reconstruction in Fusion 360.

Run through Fusion's Scripts/Add-Ins environment or fusion_mcp_execute.
The script does not save the active document.
"""

import json
import math

import adsk.core
import adsk.fusion


ASSEMBLY_NAME = "Codex_Micro_Mechanical_v0_1"
_COMPONENTS_ALLOWED = None


def _cm(mm: float) -> float:
    """Fusion API database length unit is centimetres."""
    return mm / 10.0


def _point(x_mm: float, y_mm: float, z_mm: float = 0.0) -> adsk.core.Point3D:
    return adsk.core.Point3D.create(_cm(x_mm), _cm(y_mm), _cm(z_mm))


def _identity() -> adsk.core.Matrix3D:
    return adsk.core.Matrix3D.create()


def _new_component(parent: adsk.fusion.Component, name: str) -> adsk.fusion.Component:
    global _COMPONENTS_ALLOWED
    if _COMPONENTS_ALLOWED is False:
        return parent
    try:
        occurrence = parent.occurrences.addNewComponent(_identity())
        occurrence.component.name = name
        _COMPONENTS_ALLOWED = True
        return occurrence.component
    except RuntimeError as error:
        if "Part Design documents can only contain one component" not in str(error):
            raise
        # New Fusion Part Design documents intentionally prohibit occurrences.
        # Keep separate, well-named BRep bodies in the root component instead.
        _COMPONENTS_ALLOWED = False
        return parent


def _draw_rounded_rectangle(
    sketch: adsk.fusion.Sketch,
    cx_mm: float,
    cy_mm: float,
    width_mm: float,
    depth_mm: float,
    radius_mm: float,
) -> None:
    x0 = cx_mm - width_mm / 2.0
    x1 = cx_mm + width_mm / 2.0
    y0 = cy_mm - depth_mm / 2.0
    y1 = cy_mm + depth_mm / 2.0
    r = min(radius_mm, width_mm / 2.0, depth_mm / 2.0)

    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs

    lines.addByTwoPoints(_point(x0 + r, y0), _point(x1 - r, y0))
    arcs.addByCenterStartSweep(
        _point(x1 - r, y0 + r), _point(x1 - r, y0), math.pi / 2.0
    )
    lines.addByTwoPoints(_point(x1, y0 + r), _point(x1, y1 - r))
    arcs.addByCenterStartSweep(
        _point(x1 - r, y1 - r), _point(x1, y1 - r), math.pi / 2.0
    )
    lines.addByTwoPoints(_point(x1 - r, y1), _point(x0 + r, y1))
    arcs.addByCenterStartSweep(
        _point(x0 + r, y1 - r), _point(x0 + r, y1), math.pi / 2.0
    )
    lines.addByTwoPoints(_point(x0, y1 - r), _point(x0, y0 + r))
    arcs.addByCenterStartSweep(
        _point(x0 + r, y0 + r), _point(x0, y0 + r), math.pi / 2.0
    )


def _move_bodies(
    component: adsk.fusion.Component,
    bodies: list[adsk.fusion.BRepBody],
    dx_mm: float = 0.0,
    dy_mm: float = 0.0,
    dz_mm: float = 0.0,
) -> None:
    if abs(dx_mm) + abs(dy_mm) + abs(dz_mm) < 1e-9:
        return
    entities = adsk.core.ObjectCollection.create()
    for body in bodies:
        entities.add(body)
    transform = _identity()
    transform.translation = adsk.core.Vector3D.create(
        _cm(dx_mm), _cm(dy_mm), _cm(dz_mm)
    )
    move_features = component.features.moveFeatures
    move_input = move_features.createInput2(entities)
    move_input.defineAsFreeMove(transform)
    move_features.add(move_input)


def _rotate_body_z(
    component: adsk.fusion.Component,
    body: adsk.fusion.BRepBody,
    cx_mm: float,
    cy_mm: float,
    angle_deg: float,
) -> None:
    entities = adsk.core.ObjectCollection.create()
    entities.add(body)
    transform = _identity()
    transform.setToRotation(
        math.radians(angle_deg),
        adsk.core.Vector3D.create(0.0, 0.0, 1.0),
        _point(cx_mm, cy_mm),
    )
    move_features = component.features.moveFeatures
    move_input = move_features.createInput2(entities)
    move_input.defineAsFreeMove(transform)
    move_features.add(move_input)


def _extrude_profile(
    component: adsk.fusion.Component,
    profile,
    height_mm: float,
    operation: int,
):
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, operation)
    extrude_input.setDistanceExtent(
        False, adsk.core.ValueInput.createByReal(_cm(height_mm))
    )
    return extrudes.add(extrude_input)


def _add_rounded_box(
    component: adsk.fusion.Component,
    name: str,
    cx_mm: float,
    cy_mm: float,
    z_mm: float,
    width_mm: float,
    depth_mm: float,
    height_mm: float,
    radius_mm: float,
) -> adsk.fusion.BRepBody:
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = f"{name}_profile"
    _draw_rounded_rectangle(sketch, cx_mm, cy_mm, width_mm, depth_mm, radius_mm)
    feature = _extrude_profile(
        component,
        sketch.profiles.item(0),
        height_mm,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    _move_bodies(component, [body], dz_mm=z_mm)
    return body


def _add_cylinder(
    component: adsk.fusion.Component,
    name: str,
    cx_mm: float,
    cy_mm: float,
    z_mm: float,
    diameter_mm: float,
    height_mm: float,
) -> adsk.fusion.BRepBody:
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = f"{name}_profile"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        _point(cx_mm, cy_mm), _cm(diameter_mm / 2.0)
    )
    feature = _extrude_profile(
        component,
        sketch.profiles.item(0),
        height_mm,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    _move_bodies(component, [body], dz_mm=z_mm)
    return body


def _add_ring(
    component: adsk.fusion.Component,
    name: str,
    cx_mm: float,
    cy_mm: float,
    z_mm: float,
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    height_mm: float,
) -> adsk.fusion.BRepBody:
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = f"{name}_profile"
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(_point(cx_mm, cy_mm), _cm(outer_diameter_mm / 2.0))
    circles.addByCenterRadius(_point(cx_mm, cy_mm), _cm(inner_diameter_mm / 2.0))
    annulus = None
    for index in range(sketch.profiles.count):
        candidate = sketch.profiles.item(index)
        if candidate.profileLoops.count == 2:
            annulus = candidate
            break
    feature = _extrude_profile(
        component,
        annulus,
        height_mm,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    _move_bodies(component, [body], dz_mm=z_mm)
    return body


def _add_rounded_ring(
    component: adsk.fusion.Component,
    name: str,
    z_mm: float,
    outer_width_mm: float,
    outer_depth_mm: float,
    outer_radius_mm: float,
    inner_width_mm: float,
    inner_depth_mm: float,
    inner_radius_mm: float,
    height_mm: float,
) -> adsk.fusion.BRepBody:
    outer_sketch = component.sketches.add(component.xYConstructionPlane)
    outer_sketch.name = f"{name}_outer"
    _draw_rounded_rectangle(
        outer_sketch, 0.0, 0.0, outer_width_mm, outer_depth_mm, outer_radius_mm
    )
    outer_feature = _extrude_profile(
        component,
        outer_sketch.profiles.item(0),
        height_mm,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = outer_feature.bodies.item(0)
    body.name = name

    inner_sketch = component.sketches.add(component.xYConstructionPlane)
    inner_sketch.name = f"{name}_inner"
    _draw_rounded_rectangle(
        inner_sketch, 0.0, 0.0, inner_width_mm, inner_depth_mm, inner_radius_mm
    )
    _extrude_profile(
        component,
        inner_sketch.profiles.item(0),
        height_mm,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )
    _move_bodies(component, [body], dz_mm=z_mm)
    return body


def _cut_circles(
    component: adsk.fusion.Component,
    centers_mm: list[tuple[float, float]],
    diameter_mm: float,
    depth_mm: float,
) -> None:
    sketch = component.sketches.add(component.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    for x_mm, y_mm in centers_mm:
        circles.addByCenterRadius(_point(x_mm, y_mm), _cm(diameter_mm / 2.0))
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    _extrude_profile(
        component,
        profiles,
        depth_mm,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )


def _set_parameter(
    design: adsk.fusion.Design,
    name: str,
    expression: str,
    comment: str,
) -> None:
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
        parameter.comment = comment
    else:
        design.userParameters.add(
            name,
            adsk.core.ValueInput.createByString(expression),
            "mm",
            comment,
        )


def _appearance(app: adsk.core.Application, candidate_names: list[str]):
    # The currently bundled Fusion material libraries throw on some localized
    # display names instead of returning None. Geometry must remain independent
    # of an optional rendering asset, so v0.1 leaves appearance assignment off.
    return None


def _paint(body: adsk.fusion.BRepBody, appearance) -> None:
    if appearance:
        body.appearance = appearance


def _remove_prior_assembly(root: adsk.fusion.Component) -> None:
    for index in range(root.occurrences.count - 1, -1, -1):
        occurrence = root.occurrences.item(index)
        if occurrence.component.name == ASSEMBLY_NAME:
            occurrence.deleteMe()


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    parameters = {
        "cm_case_width": ("108 mm", "MEASURED from official top render"),
        "cm_case_depth": ("108 mm", "MEASURED from official top render"),
        "cm_case_corner_radius": ("14 mm", "MEASURED from official top render"),
        "cm_key_pitch": ("19.05 mm", "CONFIRMED Work Louder MX pitch"),
        "cm_top_pcb_size": ("90 mm", "MEASURED from official top render"),
        "cm_screw_pitch": ("78 mm", "MEASURED provisional ±0.5 mm"),
        "cm_frame_bottom_z": ("5.7 mm", "INFERRED from front render"),
        "cm_frame_height": ("10.3 mm", "MEASURED provisional ±1.5 mm"),
        "cm_bottom_diameter": ("94 mm", "MEASURED provisional from bottom render"),
        "cm_bottom_front_height": ("3.8 mm", "MEASURED/INFERRED from official side views"),
        "cm_bottom_rear_height": ("12 mm", "MEASURED/INFERRED from official side views"),
        "cm_bottom_tilt": ("5 deg", "MEASURED/INFERRED from official side views"),
        "cm_pcb_z": ("14.4 mm", "Rev B POM boss support plane"),
        "cm_pcb_thickness": ("1.6 mm", "INFERRED standard PCB"),
        "cm_keycap_1u": ("17.6 mm", "MEASURED from official top render"),
        "cm_keycap_2u": ("36.55 mm", "MEASURED from pitch and gap"),
        "cm_keycap_depth": ("17.6 mm", "MEASURED from official top render"),
        "cm_keycap_height": ("7 mm", "MEASURED provisional from front render"),
        "cm_switch_body": ("15 mm", "INFERRED Gateron low-profile class"),
        "cm_switch_height": ("8 mm", "INFERRED keep-out envelope"),
        "cm_joystick_width": ("19.6 mm", "HIGH-CONFIDENCE Alps RKJXY candidate"),
        "cm_joystick_depth": ("18.1 mm", "HIGH-CONFIDENCE Alps RKJXY candidate"),
        "cm_joystick_height": ("4.9 mm", "HIGH-CONFIDENCE Alps RKJXY candidate"),
        "cm_battery_width": ("58 mm", "INFERRED packaging placeholder"),
        "cm_battery_depth": ("42 mm", "INFERRED packaging placeholder"),
        "cm_battery_height": ("6 mm", "INFERRED packaging placeholder"),
    }
    for parameter_name, (expression, comment) in parameters.items():
        _set_parameter(design, parameter_name, expression, comment)

    _remove_prior_assembly(root)
    assembly = _new_component(root, ASSEMBLY_NAME)

    clear_appearance = _appearance(
        app, ["Glass - Clear", "Plastic - Transparent", "Acrylic - Clear"]
    )
    aluminum_appearance = _appearance(
        app, ["Aluminum - Satin", "Aluminum - Anodized", "Aluminum"]
    )
    white_appearance = _appearance(
        app, ["Plastic - Matte (White)", "Paint - Enamel Glossy (White)", "White"]
    )
    black_appearance = _appearance(
        app, ["Plastic - Matte (Black)", "Rubber - Matte", "Black"]
    )
    pcb_appearance = _appearance(
        app, ["Plastic - Translucent (White)", "Paint - Enamel Glossy (White)"]
    )
    green_appearance = _appearance(app, ["LED - Green", "Green"])
    amber_appearance = _appearance(app, ["LED - Amber", "Yellow"])

    housing = _new_component(assembly, "01_Housing")
    frame_body = _add_rounded_ring(
        housing,
        "PMMA_PC_Housing_Ring_108mm",
        5.7,
        108.0,
        108.0,
        14.0,
        92.0,
        92.0,
        7.0,
        10.3,
    )
    _paint(frame_body, clear_appearance)

    bottom = _new_component(assembly, "02_Bottom")
    bottom_body = _add_cylinder(
        bottom, "CNC_Aluminum_Bottom_D94", 0.0, 0.0, 0.8, 94.0, 4.9
    )
    # Simplified visible protrusion of the purchased JIS G-65 O-ring.  The
    # production base captures the full 3.1 mm section in a 2.2 mm groove.
    rubber_ring = _add_ring(
        bottom, "Purchased_JLCMC_G65_Oring_Visible_Protrusion", 0.0, 0.0, 0.0,
        70.6, 64.4, 0.9
    )
    _paint(bottom_body, aluminum_appearance)
    _paint(rubber_ring, black_appearance)

    internals = _new_component(assembly, "03_Internal_Keepouts")
    lower_pcb = _add_rounded_box(
        internals,
        "Lower_Controller_PCB_PLACEHOLDER",
        0.0,
        24.0,
        6.2,
        68.0,
        25.0,
        1.0,
        2.0,
    )
    battery = _add_rounded_box(
        internals,
        "LiPo_1900_2100mAh_PLACEHOLDER",
        0.0,
        -17.0,
        6.2,
        58.0,
        42.0,
        6.0,
        3.0,
    )
    ffc = _add_rounded_box(
        internals,
        "FFC_Keepout",
        0.0,
        5.0,
        12.2,
        18.0,
        8.0,
        0.4,
        1.0,
    )
    _paint(lower_pcb, green_appearance)
    _paint(battery, black_appearance)
    _paint(ffc, amber_appearance)

    top_pcb = _new_component(assembly, "04_Top_PCB")
    top_pcb_body = _add_rounded_box(
        top_pcb,
        "Top_PCB_90x90x1p6",
        0.0,
        0.0,
        0.0,
        90.0,
        90.0,
        1.6,
        5.0,
    )
    screw_centers = [(-39.0, -39.0), (-39.0, 39.0), (39.0, -39.0), (39.0, 39.0)]
    _cut_circles(top_pcb, screw_centers, 3.2, 1.6)
    _move_bodies(top_pcb, [top_pcb_body], dz_mm=14.0)
    _paint(top_pcb_body, pcb_appearance)

    hardware = _new_component(assembly, "05_Hardware")
    for index, (x_mm, y_mm) in enumerate(screw_centers, 1):
        standoff = _add_ring(
            hardware,
            f"Standoff_{index}_D7_M3_clearance",
            x_mm,
            y_mm,
            5.7,
            7.0,
            3.2,
            8.3,
        )
        screw_head = _add_cylinder(
            hardware,
            f"M3_Socket_Head_{index}_envelope",
            x_mm,
            y_mm,
            15.6,
            5.5,
            3.0,
        )
        _paint(standoff, aluminum_appearance)
        _paint(screw_head, black_appearance)

    switches = _new_component(assembly, "06_Switches_12x_GLP_Footprint")
    pitch = 19.05
    x_columns = [-1.5 * pitch, -0.5 * pitch, 0.5 * pitch, 1.5 * pitch]
    y_rows = [1.5 * pitch, 0.5 * pitch, -0.5 * pitch, -1.5 * pitch]
    switch_positions = [
        (x_columns[1], y_rows[0], "Agent_R1_C2"),
        (x_columns[2], y_rows[0], "Agent_R1_C3"),
        (x_columns[0], y_rows[1], "Agent_R2_C1"),
        (x_columns[1], y_rows[1], "Agent_R2_C2"),
        (x_columns[2], y_rows[1], "Agent_R2_C3"),
        (x_columns[3], y_rows[1], "Agent_R2_C4"),
        (x_columns[0], y_rows[2], "Command_R3_C1"),
        (x_columns[1], y_rows[2], "Command_R3_C2"),
        (x_columns[2], y_rows[2], "Command_R3_C3"),
        (x_columns[3], y_rows[2], "Command_R3_C4"),
        (0.0, y_rows[3], "PushToTalk_2U"),
        (x_columns[3], y_rows[3], "Command_R4_C4"),
    ]
    for index, (x_mm, y_mm, label) in enumerate(switch_positions, 1):
        switch_body = _add_rounded_box(
            switches,
            f"SW{index:02d}_{label}",
            x_mm,
            y_mm,
            15.6,
            15.0,
            15.0,
            8.0,
            1.0,
        )
        _paint(switch_body, black_appearance)

    stabilizers = _new_component(assembly, "07_2U_Stabilizer_Keepouts")
    for index, x_mm in enumerate((-11.9, 11.9), 1):
        stabilizer = _add_rounded_box(
            stabilizers,
            f"2U_Stabilizer_{index}_PLACEHOLDER",
            x_mm,
            y_rows[3],
            15.6,
            5.0,
            12.0,
            6.0,
            0.8,
        )
        _paint(stabilizer, black_appearance)

    translucent_caps = _new_component(assembly, "08_Keycaps_Translucent_PC")
    white_caps = _new_component(assembly, "09_Keycaps_White_PBT")
    translucent_positions = switch_positions[:6]
    white_positions = switch_positions[6:10] + switch_positions[11:12]
    for index, (x_mm, y_mm, label) in enumerate(translucent_positions, 1):
        cap = _add_rounded_box(
            translucent_caps,
            f"PC_1U_{index}_{label}",
            x_mm,
            y_mm,
            22.0,
            17.6,
            17.6,
            7.0,
            3.0,
        )
        _paint(cap, clear_appearance)
    for index, (x_mm, y_mm, label) in enumerate(white_positions, 1):
        cap = _add_rounded_box(
            white_caps,
            f"PBT_1U_{index}_{label}",
            x_mm,
            y_mm,
            22.0,
            17.6,
            17.6,
            7.0,
            3.0,
        )
        _paint(cap, white_appearance)
    cap_2u = _add_rounded_box(
        white_caps,
        "PBT_2U_PushToTalk",
        0.0,
        y_rows[3],
        22.0,
        36.55,
        17.6,
        7.0,
        3.0,
    )
    _paint(cap_2u, white_appearance)

    controls = _new_component(assembly, "10_Controls")
    encoder_body = _add_rounded_box(
        controls,
        "Clickable_Encoder_Body_PLACEHOLDER",
        x_columns[0],
        y_rows[0],
        15.6,
        14.0,
        14.0,
        6.0,
        1.5,
    )
    encoder_shaft = _add_cylinder(
        controls,
        "Encoder_Shaft_D6",
        x_columns[0],
        y_rows[0],
        21.6,
        6.0,
        7.0,
    )
    knob = _add_cylinder(
        controls,
        "Codex_Dial_D19",
        x_columns[0],
        y_rows[0],
        22.0,
        19.0,
        12.0,
    )
    knob_fin = _add_rounded_box(
        controls,
        "Codex_Dial_Raised_Fin",
        x_columns[0],
        y_rows[0],
        32.0,
        16.0,
        4.0,
        8.0,
        1.0,
    )
    _rotate_body_z(controls, knob_fin, x_columns[0], y_rows[0], 45.0)
    for body in (encoder_body, encoder_shaft, knob, knob_fin):
        _paint(body, white_appearance)

    joystick_base = _add_rounded_box(
        controls,
        "Planar_Joystick_RKJXY_CANDIDATE",
        x_columns[3],
        y_rows[0],
        15.6,
        19.6,
        18.1,
        4.9,
        2.0,
    )
    joystick_cap = _add_cylinder(
        controls,
        "Rubber_Joystick_Cap_D14p5",
        x_columns[3],
        y_rows[0],
        21.0,
        14.5,
        7.0,
    )
    touch_disc = _add_cylinder(
        controls,
        "Capacitive_Touch_Area_D14p5",
        x_columns[0],
        y_rows[3],
        15.61,
        14.5,
        0.45,
    )
    _paint(joystick_base, black_appearance)
    _paint(joystick_cap, black_appearance)
    _paint(touch_disc, black_appearance)

    for index, y_mm in enumerate((-24.575, -28.575, -32.575), 1):
        indicator = _add_rounded_box(
            controls,
            f"Layer_LED_{index}",
            -39.5,
            y_mm,
            15.62,
            2.2,
            1.3,
            0.6,
            0.25,
        )
        _paint(indicator, amber_appearance if index > 1 else white_appearance)

    io = _new_component(assembly, "11_IO_Keepouts")
    usb_c = _add_rounded_box(
        io,
        "USB_C_Receptacle_Keepout",
        0.0,
        43.5,
        7.0,
        9.2,
        7.5,
        3.4,
        1.2,
    )
    rear_button = _add_cylinder(
        io,
        "Rear_Power_Button_D3p5",
        14.0,
        49.5,
        9.0,
        3.5,
        3.0,
    )
    _paint(usb_c, aluminum_appearance)
    _paint(rear_button, black_appearance)

    app.activeViewport.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    app.activeViewport.fit()

    print(
        json.dumps(
            {
                "assembly": ASSEMBLY_NAME,
                "outer_mm": [108.0, 108.0],
                "top_pcb_mm": [90.0, 90.0, 1.6],
                "keyboard_switches": 12,
                "published_mechanical_switch_count_including_encoder_push": 13,
                "key_pitch_mm": 19.05,
                "fusion_structure": (
                    "nested components" if _COMPONENTS_ALLOWED else "named bodies in Part Design"
                ),
                "status": "mechanical reconstruction created; document not saved",
            }
        )
    )
