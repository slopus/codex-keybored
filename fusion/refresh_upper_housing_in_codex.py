"""Refresh CM2-001 BaseFeature in Codex from its latest verified STEP."""

import json

import adsk.core
import adsk.fusion


STEP = "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-001_upper_housing.step"
FEATURE = "MFG_CM2_001_Upper_Housing_PC_or_Wood"


def _cm(mm):
    return mm / 10.0


def _all_bodies(root):
    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    for i in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(i)
        bodies.extend(occurrence.bRepBodies.item(j) for j in range(occurrence.bRepBodies.count))
    return bodies


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

    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(0, 0, _cm(5.7))
    if not manager.transform(transient, transform):
        raise RuntimeError("Upper housing transform failed")

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

    parameter = design.userParameters.itemByName("mfg_bottom_boss_height")
    if parameter:
        parameter.expression = "6 mm"
        parameter.comment = "Integrated M2.5 bottom fastener bosses"
    else:
        design.userParameters.add(
            "mfg_bottom_boss_height",
            adsk.core.ValueInput.createByString("6 mm"),
            "mm",
            "Integrated M2.5 bottom fastener bosses",
        )
    print(json.dumps({
        "status": "CM2-001 refreshed from STEP",
        "feature": FEATURE,
        "bottom_boss_height_mm": 6.0,
    }))
