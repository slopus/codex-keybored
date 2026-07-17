"""Refresh CM2-002 BaseFeature in Codex from the latest verified wedge STEP."""

import json

import adsk.core
import adsk.fusion


STEP = "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-002_bottom_weight.step"
FEATURE = "MFG_CM2_002_Bottom_Weight_6061"


def _cm(mm):
    return mm / 10.0


def _all_bodies(root):
    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    for i in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(i)
        bodies.extend(
            occurrence.bRepBodies.item(j)
            for j in range(occurrence.bRepBodies.count)
        )
    return bodies


def _set_parameter(design, name, expression, comment):
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
        parameter.comment = comment
    else:
        design.userParameters.add(
            name,
            adsk.core.ValueInput.createByString(expression),
            "mm" if "deg" not in expression else "deg",
            comment,
        )


def run(_context: str):
    app = adsk.core.Application.get()
    original = app.activeDocument
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    feature = root.features.baseFeatures.itemByName(FEATURE)
    if feature is None:
        raise RuntimeError("BaseFeature not found: " + FEATURE)

    options = app.importManager.createSTEPImportOptions(STEP)
    source_document = app.importManager.importToNewDocument(options)
    try:
        source_design = adsk.fusion.Design.cast(app.activeProduct)
        bodies = _all_bodies(source_design.rootComponent)
        if len(bodies) != 1:
            raise RuntimeError(f"Expected one STEP body; got {len(bodies)}")
        manager = adsk.fusion.TemporaryBRepManager.get()
        transient = manager.copy(bodies[0])
    finally:
        original.activate()
        source_document.close(False)

    # Exported wedge top is Z=12.0; align it with the housing datum Z=5.7.
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(0, 0, _cm(-6.3))
    if not manager.transform(transient, transform):
        raise RuntimeError("Bottom weight transform failed")

    if not feature.startEdit():
        raise RuntimeError("Could not edit: " + FEATURE)
    try:
        source_bodies = feature.sourceBodies
        if len(source_bodies) != 1:
            raise RuntimeError(f"Expected one source body; got {len(source_bodies)}")
        if not feature.updateBody(source_bodies[0], transient):
            raise RuntimeError("BaseFeature.updateBody failed")
    finally:
        feature.finishEdit()

    _set_parameter(design, "mfg_bottom_weight_front_height", "3.8 mm", "CM2-002 wedge")
    _set_parameter(design, "mfg_bottom_weight_rear_height", "12 mm", "CM2-002 wedge")
    _set_parameter(
        design,
        "mfg_bottom_weight_tilt",
        "5 deg",
        "Measured/inferred from official side views",
    )

    app.activeViewport.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    app.activeViewport.fit()
    print(json.dumps({
        "status": "CM2-002 refreshed from wedge STEP",
        "feature": FEATURE,
        "diameter_mm": 94.0,
        "front_thickness_mm": 3.8,
        "rear_thickness_mm": 12.0,
        "tilt_deg": 5.0,
        "mounting_face_z_mm": 5.7,
    }))
