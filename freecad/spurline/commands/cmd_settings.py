"""
SpurLine — Settings command.

Registers the 'SpurLine_Settings' FreeCAD command, which opens a
dialog to configure LightBurn and MillMage endpoint strings.
"""

import FreeCADGui


class SpurLine_Settings:
    """FreeCAD command: open the SpurLine connection settings dialog."""

    def GetResources(self) -> dict:
        return {
            "MenuText": "Settings...",
            "ToolTip":  "Configure LightBurn and MillMage connection strings",
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self):
        from freecad.spurline.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(parent=FreeCADGui.getMainWindow())
        dlg.exec_()


FreeCADGui.addCommand("SpurLine_Settings", SpurLine_Settings())
