"""
SpurLine — Timing Belt Pulley command.

Registers the 'SpurLine_Timing' FreeCAD command.
"""

import FreeCAD
import FreeCADGui


class SpurLine_Timing:
    """
    FreeCAD command: create a timing belt pulley profile.

    Exposes belt-type selection (GT2, T5, T2.5, etc.) in the panel
    in place of the module / pressure-angle fields used for involute gears.
    """

    def GetResources(self) -> dict:
        return {
            "Pixmap":   "resources/icons/timing.svg",
            "MenuText": "Timing Belt Pulley",
            "ToolTip":  "Generate a 2D timing belt pulley profile",
        }

    def IsActive(self) -> bool:
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        from freecad.spurline.ui.gear_panel import GearPanel
        panel = GearPanel(gear_type="timing")
        FreeCADGui.Control.showDialog(panel)


FreeCADGui.addCommand("SpurLine_Timing", SpurLine_Timing())
