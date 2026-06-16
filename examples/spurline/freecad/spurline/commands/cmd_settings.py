"""
SpurLine — Reset authorizations command.

Clears stored shared secrets so the user is re-prompted for consent
in LightBurn / MillMage on the next send.
"""

import FreeCADGui


class SpurLine_Settings:
    """FreeCAD command: clear stored connection secrets."""

    def GetResources(self) -> dict:
        return {
            "MenuText": "Reset authorizations",
            "ToolTip":  "Clear stored connection secrets — you will need to re-approve in LightBurn / MillMage",
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self):
        try:
            from PySide2 import QtWidgets
        except ImportError:
            from PySide6 import QtWidgets

        answer = QtWidgets.QMessageBox.question(
            FreeCADGui.getMainWindow(),
            "SpurLine — Reset authorizations",
            "Clear stored connection secrets?\n\n"
            "You will need to re-approve SpurLine in LightBurn / MillMage "
            "the next time you send.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if answer == QtWidgets.QMessageBox.Yes:
            from freecad.spurline.prefs.preferences import SpurLinePrefs
            SpurLinePrefs().clear_all_secrets()


FreeCADGui.addCommand("SpurLine_Settings", SpurLine_Settings())
