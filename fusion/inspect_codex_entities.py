import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("Active product is not a Fusion Design")
    root = design.rootComponent
    print(f"rootBodies={root.bRepBodies.count}")
    for i in range(root.bRepBodies.count):
        body = root.bRepBodies.item(i)
        print(f"rootBody[{i}] name={body.name!r} visible={body.isVisible}")
    print(f"occurrences={root.allOccurrences.count}")
    for i in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(i)
        print(f"occ[{i}] name={occurrence.name!r} bodies={occurrence.bRepBodies.count}")
        for j in range(occurrence.bRepBodies.count):
            body = occurrence.bRepBodies.item(j)
            print(f"occBody[{i},{j}] name={body.name!r} visible={body.isVisible}")
    print(f"baseFeatures={root.features.baseFeatures.count}")
    for i in range(root.features.baseFeatures.count):
        feature = root.features.baseFeatures.item(i)
        print(f"baseFeature[{i}] name={feature.name!r} bodies={feature.bodies.count}")
