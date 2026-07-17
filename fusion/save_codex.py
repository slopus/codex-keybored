"""Save the active Codex Fusion document after verified project updates."""

import json

import adsk.core


def run(_context):
    app = adsk.core.Application.get()
    document = app.activeDocument
    if document.name != "Codex":
        raise RuntimeError("Expected active document Codex; got " + document.name)
    document.save("")
    print(json.dumps({"status": "saved", "document": document.name}))
