"""
SpurLine — Involute Rack command.

Registers the 'SpurLine_Rack' FreeCAD command.
"""

import FreeCAD
import FreeCADGui


class SpurLine_Rack:
    """
    FreeCAD command: create an involute rack profile.

    Racks are linear (not circular) so the bore / keyway options
    will be hidden in the panel when gear_type='rack'.
    """

    def GetResources(self) -> dict:
        return {
            "Pixmap":   "resources/icons/rack.svg",
            "MenuText": "Involute Rack",
            "ToolTip":  "Generate a 2D involute rack profile",
        }

    def IsActive(self) -> bool:
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        from freecad.spurline.ui.gear_panel import GearPanel
        panel = GearPanel(gear_type="rack")
        FreeCADGui.Control.showDialog(panel)


FreeCADGui.addCommand("SpurLine_Rack", SpurLine_Rack())
