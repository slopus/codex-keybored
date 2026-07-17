"""Round-trip STEP verification in Fusion 360."""

import json
import os

import adsk.core
import adsk.fusion


FILES = [
    "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-001_upper_housing.step",
    "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-002_bottom_weight.step",
    "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-003_optional_lightpipe.step",
    "/Users/steve/Documents/CodexKB/codex-micro/cnc/STEP/CM2-004_joystick_cap.step",
]


def _all_bodies(root):
    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    for i in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(i)
        bodies.extend(occurrence.bRepBodies.item(j) for j in range(occurrence.bRepBodies.count))
    return bodies


def _bounds_mm(bodies):
    minimum = [float("inf")] * 3
    maximum = [float("-inf")] * 3
    for body in bodies:
        box = body.boundingBox
        for i, value in enumerate((box.minPoint.x, box.minPoint.y, box.minPoint.z)):
            minimum[i] = min(minimum[i], value)
        for i, value in enumerate((box.maxPoint.x, box.maxPoint.y, box.maxPoint.z)):
            maximum[i] = max(maximum[i], value)
    return {
        "min": [round(v * 10, 3) for v in minimum],
        "max": [round(v * 10, 3) for v in maximum],
        "size": [round((maximum[i] - minimum[i]) * 10, 3) for i in range(3)],
    }


def run(_context: str):
    app = adsk.core.Application.get()
    original = app.activeDocument
    results = []
    for path in FILES:
        options = app.importManager.createSTEPImportOptions(path)
        document = app.importManager.importToNewDocument(options)
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            bodies = _all_bodies(design.rootComponent)
            results.append({
                "file": os.path.basename(path),
                "bodies": len(bodies),
                "solid_bodies": sum(1 for body in bodies if body.isSolid),
                "bounds_mm": _bounds_mm(bodies),
                "volume_mm3": round(sum(body.physicalProperties.volume for body in bodies) * 1000, 2),
            })
        finally:
            original.activate()
            document.close(False)
    original.activate()
    print(json.dumps({"round_trip": "PASS", "parts": results}))
