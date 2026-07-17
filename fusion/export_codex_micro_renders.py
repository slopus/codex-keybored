import adsk.core
import adsk.fusion


OUTPUT_DIR = "/Users/steve/Documents/CodexKB/codex-micro/docs/assets/renders"

PRODUCTION_FEATURES = {
    "upper": "MFG_CM2_001_Upper_Housing_PC_or_Wood",
    "bottom": "MFG_CM2_002_Bottom_Weight_6061",
    "lightpipe": "MFG_CM2_003_Optional_Lightpipe_PMMA",
    "cap": "MFG_CM2_004_Joystick_Cap_POM_or_TPU",
}


def _all_bodies(design):
    root = design.rootComponent
    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    for i in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(i)
        bodies.extend(
            occurrence.bRepBodies.item(j)
            for j in range(occurrence.bRepBodies.count)
        )
    return bodies


def _set_visibility(bodies, visible_tokens):
    for body in bodies:
        body.isVisible = body.entityToken in visible_tokens


def _save_view(viewport, filename, orientation):
    camera = viewport.camera
    camera.viewOrientation = orientation
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    adsk.doEvents()

    options = adsk.core.SaveImageFileOptions.create(f"{OUTPUT_DIR}/{filename}")
    options.width = 1800
    options.height = 1350
    options.isBackgroundTransparent = False
    options.isAntiAliased = True
    if not viewport.saveAsImageFileWithOptions(options):
        raise RuntimeError(f"Failed to save {filename}")
    print(f"saved:{filename}")


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("Active Fusion document is not a Design")

    viewport = app.activeViewport
    bodies = _all_bodies(design)
    original_visibility = {body.entityToken: body.isVisible for body in bodies}
    original_camera = viewport.camera

    feature_by_name = {
        root_feature.name: root_feature
        for root_feature in (
            design.rootComponent.features.baseFeatures.item(i)
            for i in range(design.rootComponent.features.baseFeatures.count)
        )
    }
    missing = sorted(set(PRODUCTION_FEATURES.values()) - set(feature_by_name))
    if missing:
        raise RuntimeError("Missing production BaseFeatures: " + ", ".join(missing))

    production_bodies = {}
    for key, feature_name in PRODUCTION_FEATURES.items():
        feature = feature_by_name[feature_name]
        if feature.bodies.count != 1:
            raise RuntimeError(f"Expected one body in {feature_name}; got {feature.bodies.count}")
        production_bodies[key] = feature.bodies.item(0)

    try:
        # Full assembly: preserve the useful conceptual electronics/controls,
        # but replace the old flat conceptual shell/bottom/cap with production
        # bodies.  The optional lightpipe is rendered separately.
        assembly_tokens = {
            body.entityToken
            for body in bodies
            if original_visibility.get(body.entityToken, False)
            and body.name not in {
                "PMMA_PC_Housing_Ring_108mm",
                "CNC_Aluminum_Bottom_D94",
                "AntiSlip_Ring_D92_D82",
                "Rubber_Joystick_Cap_D14p5",
            }
        }
        assembly_tokens.update({
            production_bodies["upper"].entityToken,
            production_bodies["bottom"].entityToken,
            production_bodies["cap"].entityToken,
        })
        assembly_tokens.discard(production_bodies["lightpipe"].entityToken)
        _set_visibility(bodies, assembly_tokens)
        _save_view(
            viewport,
            "fusion-codex-assembly-iso.png",
            adsk.core.ViewOrientations.IsoTopRightViewOrientation,
        )
        _save_view(
            viewport,
            "fusion-codex-assembly-top.png",
            adsk.core.ViewOrientations.TopViewOrientation,
        )
        _save_view(
            viewport,
            "fusion-codex-assembly-side.png",
            adsk.core.ViewOrientations.RightViewOrientation,
        )

        renders = [
            ("upper", "fusion-cm2-001-upper-housing.png", adsk.core.ViewOrientations.IsoTopRightViewOrientation),
            ("bottom", "fusion-cm2-002-bottom-weight.png", adsk.core.ViewOrientations.IsoTopRightViewOrientation),
            ("bottom", "fusion-cm2-002-bottom-weight-side.png", adsk.core.ViewOrientations.RightViewOrientation),
            ("lightpipe", "fusion-cm2-003-lightpipe.png", adsk.core.ViewOrientations.TopViewOrientation),
            ("cap", "fusion-cm2-004-joystick-cap.png", adsk.core.ViewOrientations.IsoTopRightViewOrientation),
        ]
        for key, filename, orientation in renders:
            _set_visibility(bodies, {production_bodies[key].entityToken})
            _save_view(viewport, filename, orientation)
    finally:
        for body in bodies:
            if body.entityToken in original_visibility:
                body.isVisible = original_visibility[body.entityToken]
        viewport.camera = original_camera
        viewport.refresh()
        adsk.doEvents()

    print("render-export-complete")
