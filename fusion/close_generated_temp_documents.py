"""Close only unsaved CM2 manufacturing scratch documents."""

import adsk.core


def run(_context: str):
    app = adsk.core.Application.get()
    closed = []
    for index in range(app.documents.count - 1, -1, -1):
        document = app.documents.item(index)
        if document.name.startswith("CM2-") and not document.isSaved:
            closed.append(document.name)
            document.close(False)
    print(", ".join(closed))
