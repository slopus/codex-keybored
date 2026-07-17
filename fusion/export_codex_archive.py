import adsk.core
import adsk.fusion
import traceback


TARGET = "/Users/steve/Documents/CodexKB/codex-micro/fusion/Codex_Micro_RevA.f3d"


def run(_context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        document = next((doc for doc in app.documents if doc.name == "Codex"), None)
        if document is None:
            raise RuntimeError("Fusion document 'Codex' is not open")
        document.activate()
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        if design is None:
            design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            raise RuntimeError("Codex does not contain a Fusion design product")
        options = design.exportManager.createFusionArchiveExportOptions(TARGET)
        if not design.exportManager.execute(options):
            raise RuntimeError("Fusion archive export returned false")
        print(f"Exported {TARGET}")
    except Exception:
        message = traceback.format_exc()
        print(message)
        ui.messageBox(message, "Codex archive export failed")
        raise


run(None)
