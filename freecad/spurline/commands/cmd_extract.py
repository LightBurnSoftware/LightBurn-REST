"""
SpurLine — Extract Profile from Selection command.

Registers the 'SpurLine_Extract' FreeCAD command, which extracts 2D
profiles from selected document objects (FCGear, imported STEP, etc.)
and opens the ExtractPanel for preview and sending.
"""

import FreeCAD
import FreeCADGui


class SpurLine_Extract:
    """
    FreeCAD command: extract 2D profiles from the current selection.

    The toolbar button is active only when there is an active document
    and at least one object is selected.  The selection is captured at
    activation time so it remains stable while the panel is open.
    """

    def GetResources(self) -> dict:
        return {
            "Pixmap":   "resources/icons/extract.svg",
            "MenuText": "Extract Profile from Selection",
            "ToolTip":  "Extract 2D profiles from selected objects and send to LightBurn / MillMage",
        }

    def IsActive(self) -> bool:
        return (
            FreeCAD.ActiveDocument is not None
            and bool(FreeCADGui.Selection.getSelection())
        )

    def Activated(self):
        from freecad.spurline.ui.extract_panel import ExtractPanel
        selection = FreeCADGui.Selection.getSelection()
        panel = ExtractPanel(selection)
        FreeCADGui.Control.showDialog(panel)


FreeCADGui.addCommand("SpurLine_Extract", SpurLine_Extract())
