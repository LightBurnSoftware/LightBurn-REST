"""
SpurLine — Involute Spur Gear command.

Registers the 'SpurLine_Involute' FreeCAD command, which opens the
GearPanel task panel pre-configured for involute spur gears.
"""

import FreeCAD
import FreeCADGui


class SpurLine_Involute:
    """
    FreeCAD command: create an involute spur gear profile.

    Clicking the toolbar button opens the GearPanel task panel with
    gear_type='involute'.  All geometry work happens in the panel's
    accept() method, not here.
    """

    # ------------------------------------------------------------------
    # FreeCAD command protocol
    # ------------------------------------------------------------------

    def GetResources(self) -> dict:
        """Return icon, menu label, and tooltip for this command."""
        return {
            "Pixmap":   "resources/icons/involute.svg",
            "MenuText": "Involute Spur Gear",
            "ToolTip":  "Generate a 2D involute spur gear profile",
        }

    def IsActive(self) -> bool:
        """
        Enable the button only when there is an active document.
        FreeCAD calls this to grey-out / enable the toolbar button.
        """
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        """Open the gear task panel for involute gears."""
        from freecad.spurline.ui.gear_panel import GearPanel
        panel = GearPanel(gear_type="involute")
        FreeCADGui.Control.showDialog(panel)


FreeCADGui.addCommand("SpurLine_Involute", SpurLine_Involute())
