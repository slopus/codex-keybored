"""Install verified production STEP bodies into the active Codex Fusion design."""

import json

import adsk.core
import adsk.fusion


PARTS = [
    (
        "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-001_upper_housing.step",
        "MFG_CM2_001_Upper_Housing_Black_POM_RevB",
        (0.0, 0.0, 5.7),
        True,
    ),
    (
        "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-002_bottom_weight.step",
        "MFG_CM2_002_Bottom_Weight_6061",
        # The wedge STEP has a flat mounting face at Z=12.0 mm.  Place that
        # face at the housing datum Z=5.7 mm.
        (0.0, 0.0, -6.3),
        True,
    ),
    (
        "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-003_lightpipe.step",
        "MFG_CM2_003_Mandatory_Lightpipe_PMMA_RevB",
        # The upper housing starts at Z=5.7; its light-guide pocket floor is
        # 8.8 mm above that datum.
        (0.0, 0.0, 14.5),
        True,
    ),
    (
        "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-004_joystick_cap.step",
        "MFG_CM2_004_Joystick_Cap_POM_or_TPU",
        (28.575, 28.575, 21.0),
        True,
    ),
]


def _cm(mm):
    return mm / 10.0


def _set_parameter(design, name, expression, comment):
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


def _move_bodies(root, bodies, xyz_mm):
    collection = adsk.core.ObjectCollection.create()
    for body in bodies:
        collection.add(body)
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(
        _cm(xyz_mm[0]), _cm(xyz_mm[1]), _cm(xyz_mm[2])
    )
    move_input = root.features.moveFeatures.createInput2(collection)
    move_input.defineAsFreeMove(transform)
    root.features.moveFeatures.add(move_input)


def _all_bodies(root):
    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    for i in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(i)
        bodies.extend(occurrence.bRepBodies.item(j) for j in range(occurrence.bRepBodies.count))
    return bodies


def _import_body_as_base_feature(app, original_document, root, path, name, translation):
    """Round-trip through a scratch document, then persist one transient body."""
    options = app.importManager.createSTEPImportOptions(path)
    source_document = app.importManager.importToNewDocument(options)
    try:
        source_design = adsk.fusion.Design.cast(app.activeProduct)
        source_bodies = _all_bodies(source_design.rootComponent)
        if len(source_bodies) != 1:
            raise RuntimeError(f"Expected one STEP body for {name}; got {len(source_bodies)}")
        manager = adsk.fusion.TemporaryBRepManager.get()
        transient = manager.copy(source_bodies[0])
    finally:
        original_document.activate()
        source_document.close(False)

    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(
        _cm(translation[0]), _cm(translation[1]), _cm(translation[2])
    )
    if not manager.transform(transient, transform):
        raise RuntimeError("Transient body transform failed: " + name)

    base_feature = root.features.baseFeatures.add()
    base_feature.name = name
    if not base_feature.startEdit():
        raise RuntimeError("Could not edit BaseFeature: " + name)
    try:
        body = root.bRepBodies.add(transient, base_feature)
    finally:
        base_feature.finishEdit()
    if body is None:
        raise RuntimeError("Could not persist STEP body: " + name)
    return body


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    old_hidden = []
    for body in _all_bodies(root):
        if (
            body.name in {
                "PMMA_PC_Housing_Ring_108mm",
                "CNC_Aluminum_Bottom_D94",
                "Rubber_Joystick_Cap_D14p5",
            }
            or body.name.startswith("Standoff_")
        ):
            body.isVisible = False
            old_hidden.append(body.name)

    installed = []
    original_document = app.activeDocument
    for path, name, translation, visible in PARTS:
        body = _import_body_as_base_feature(
            app, original_document, root, path, name, translation
        )
        body.name = name
        body.isVisible = visible
        installed.append(name)

    params = {
        "mfg_upper_housing_height": ("10.3 mm", "CNC STEP CM2-001"),
        "mfg_bottom_weight_diameter": ("94 mm", "CNC STEP CM2-002"),
        "mfg_bottom_weight_front_height": ("3.8 mm", "CNC STEP CM2-002 wedge"),
        "mfg_bottom_weight_rear_height": ("12 mm", "CNC STEP CM2-002 wedge"),
        "mfg_bottom_weight_tilt": ("5 deg", "Measured/inferred from official side views"),
        "mfg_top_boss_diameter": ("16 mm", "Integrated PCB bosses"),
        "mfg_top_thread_pilot": ("2.5 mm", "Tap M3x0.5 directly in black POM"),
        "mfg_bottom_screw_pitch_radius": ("41 mm", "Four M2.5 bottom screws at cardinal points"),
        "mfg_usb_cutout_width": ("11 mm", "Rear open-top USB-C capsule cutout"),
        "mfg_usb_cutout_height": ("4.6 mm", "Rear USB-C capsule cutout"),
        "mfg_lightpipe_thickness": ("1.5 mm", "Mandatory captured PMMA light guide"),
        "mfg_oring_id": ("64.4 mm", "Purchased JLCMC AMFG-P5-A65-65, JIS G-65"),
        "mfg_oring_cross_section": ("3.1 mm", "Black NBR 65A continuous anti-slip ring"),
        "mfg_oring_groove_center_diameter": ("67.5 mm", "Machined in the sloped aluminum underside"),
        "mfg_oring_groove_width": ("3.6 mm", "0.25 mm nominal side clearance per side"),
        "mfg_oring_groove_depth": ("2.2 mm", "0.9 mm nominal rubber protrusion"),
    }
    for name, (expression, comment) in params.items():
        _set_parameter(design, name, expression, comment)

    app.activeViewport.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    app.activeViewport.fit()
    print(json.dumps({
        "status": "production bodies installed in Codex; save separately",
        "installed": installed,
        "hidden_concept_bodies": old_hidden,
        "root_bodies": root.bRepBodies.count,
        "parameters": list(params.keys()),
    }))
