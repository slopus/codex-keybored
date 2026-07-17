"""Restore the photographed Codex Micro 12-key/control layout in Codex once.

The official high-resolution OpenAI render shows six translucent agent keys,
four 1U command keys, one 2U command key and one final 1U key.  The published
13-switch figure includes the rotary encoder's push switch.
"""

import json

import adsk.core
import adsk.fusion


MIGRATION_PARAMETER = "cm_layout_v3_verified_from_official_render"


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


def _retire(body):
    if body is None:
        return False
    body.name = "OBSOLETE_LAYOUT_V2_" + body.name
    body.isVisible = False
    return True


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("Active Fusion document is not a Design")
    root = design.rootComponent

    if design.userParameters.itemByName(MIGRATION_PARAMETER):
        print(json.dumps({"status": "layout v3 already applied; no changes"}))
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
            for name, body in zip(
                encoder_names + joystick_names, encoder_bodies + joystick_bodies
            )
            if body is None
        ]
        raise RuntimeError("Missing control bodies: " + ", ".join(missing))

    # Undo v2: verified official layout is encoder C1 and joystick C4.
    _move(root, encoder_bodies, dx_mm=-57.15)
    _move(root, joystick_bodies, dx_mm=57.15)

    cap_feature = root.features.baseFeatures.itemByName(
        "MFG_CM2_004_Joystick_Cap_POM_or_TPU"
    )
    if cap_feature and cap_feature.bodies.count == 1:
        _move(root, [cap_feature.bodies.item(0)], dx_mm=57.15)

    retired = []
    for name in ("SW12_Command_R4_C3", "PBT_1U_5_Command_R4_C3"):
        if _retire(_body_by_name(root, name)):
            retired.append(name)

    sw_c4 = _body_by_name(root, "SW13_Command_R4_C4")
    if sw_c4:
        sw_c4.name = "SW12_Command_R4_C4"
    cap_c4 = _body_by_name(root, "PBT_1U_6_Command_R4_C4")
    if cap_c4:
        cap_c4.name = "PBT_1U_5_Command_R4_C4"

    design.userParameters.add(
        MIGRATION_PARAMETER,
        adsk.core.ValueInput.createByString("1"),
        "",
        "Verified official 12-key layout; encoder left and joystick right",
    )
    app.activeViewport.viewOrientation = (
        adsk.core.ViewOrientations.IsoTopRightViewOrientation
    )
    app.activeViewport.fit()
    print(json.dumps({
        "status": "layout v3 applied",
        "keyboard_switches": 12,
        "published_switch_count_including_encoder_push": 13,
        "row1": ["encoder", "switch", "switch", "joystick"],
        "row4": ["touch", "centered 2U", "1U"],
        "retired_v2_bodies": retired,
    }))
