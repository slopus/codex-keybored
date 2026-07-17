"""Apply the official 13-switch/control layout correction to Codex once."""

import json

import adsk.core
import adsk.fusion


MIGRATION_PARAMETER = "cm_layout_v2_applied"


def _cm(mm):
    return mm / 10.0


def _bodies(root):
    return [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]


def _body_by_name(root, name):
    for body in _bodies(root):
        if body.name == name:
            return body
    return None


def _move(root, bodies, dx_mm=0.0, dy_mm=0.0, dz_mm=0.0):
    entities = adsk.core.ObjectCollection.create()
    for body in bodies:
        if body is not None:
            entities.add(body)
    if entities.count == 0:
        return
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(
        _cm(dx_mm), _cm(dy_mm), _cm(dz_mm)
    )
    move_input = root.features.moveFeatures.createInput2(entities)
    move_input.defineAsFreeMove(transform)
    root.features.moveFeatures.add(move_input)


def _add_box(root, name, cx_mm, cy_mm, z_mm, width_mm, depth_mm, height_mm):
    manager = adsk.fusion.TemporaryBRepManager.get()
    center = adsk.core.Point3D.create(
        _cm(cx_mm), _cm(cy_mm), _cm(z_mm + height_mm / 2.0)
    )
    x_axis = adsk.core.Vector3D.create(1, 0, 0)
    y_axis = adsk.core.Vector3D.create(0, 1, 0)
    box = adsk.core.OrientedBoundingBox3D.create(
        center,
        x_axis,
        y_axis,
        _cm(width_mm),
        _cm(depth_mm),
        _cm(height_mm),
    )
    transient = manager.createBox(box)
    base_feature = root.features.baseFeatures.add()
    base_feature.name = "LAYOUT_V2_" + name
    if not base_feature.startEdit():
        raise RuntimeError("Could not edit BaseFeature for " + name)
    try:
        body = root.bRepBodies.add(transient, base_feature)
    finally:
        base_feature.finishEdit()
    body.name = name
    body.isVisible = True
    return body


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    already = design.userParameters.itemByName(MIGRATION_PARAMETER)
    if already:
        print(json.dumps({"status": "layout v2 already applied; no changes"}))
        return

    encoder_names = [
        "Clickable_Encoder_Body_PLACEHOLDER",
        "Encoder_Shaft_D6",
        "Codex_Dial_D19",
        "Codex_Dial_Raised_Fin",
    ]
    joystick_names = [
        "Planar_Joystick_RKJXY_CANDIDATE",
        "Rubber_Joystick_Cap_D14p5",
    ]
    encoder_bodies = [_body_by_name(root, name) for name in encoder_names]
    joystick_bodies = [_body_by_name(root, name) for name in joystick_names]
    if any(body is None for body in encoder_bodies + joystick_bodies):
        missing = [
            name
            for name, body in zip(encoder_names + joystick_names, encoder_bodies + joystick_bodies)
            if body is None
        ]
        raise RuntimeError("Missing control bodies: " + ", ".join(missing))

    # Official top view: planar joystick at C1, switches at C2/C3, encoder C4.
    _move(root, encoder_bodies, dx_mm=57.15)
    _move(root, joystick_bodies, dx_mm=-57.15)

    cap_feature = root.features.baseFeatures.itemByName(
        "MFG_CM2_004_Joystick_Cap_POM_or_TPU"
    )
    if cap_feature and cap_feature.bodies.count == 1:
        _move(root, [cap_feature.bodies.item(0)], dx_mm=-57.15)

    old_sw12 = _body_by_name(root, "SW12_Command_R4_C4")
    if old_sw12:
        old_sw12.name = "SW13_Command_R4_C4"
    old_cap5 = _body_by_name(root, "PBT_1U_5_Command_R4_C4")
    if old_cap5:
        old_cap5.name = "PBT_1U_6_Command_R4_C4"

    if _body_by_name(root, "SW12_Command_R4_C3") is None:
        _add_box(
            root,
            "SW12_Command_R4_C3",
            9.525,
            -28.575,
            15.6,
            15.0,
            15.0,
            8.0,
        )
    if _body_by_name(root, "PBT_1U_5_Command_R4_C3") is None:
        _add_box(
            root,
            "PBT_1U_5_Command_R4_C3",
            9.525,
            -28.575,
            22.0,
            17.6,
            17.6,
            7.0,
        )

    design.userParameters.add(
        MIGRATION_PARAMETER,
        adsk.core.ValueInput.createByString("1"),
        "",
        "Official 13-switch layout and joystick/encoder positions corrected",
    )
    app.activeViewport.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    app.activeViewport.fit()
    print(json.dumps({
        "status": "layout v2 applied",
        "switches": 13,
        "row1": ["joystick", "switch", "switch", "encoder"],
        "added": ["SW12_Command_R4_C3", "PBT_1U_5_Command_R4_C3"],
    }))
