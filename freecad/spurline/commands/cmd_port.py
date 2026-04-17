"""
SpurLine — Set port command.

Lets the user change the localhost port that SpurLine connects to.
Changing the port clears stored secrets since the new port is a
different server instance.
"""

import FreeCAD
import FreeCADGui


class SpurLine_Port:
    """FreeCAD command: configure the localhost port."""

    def GetResources(self) -> dict:
        return {
            "MenuText": "Set port...",
            "ToolTip":  "Set the localhost port for LightBurn / MillMage",
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self):
        try:
            from PySide2 import QtWidgets
        except ImportError:
            from PySide6 import QtWidgets

        from freecad.spurline.prefs.preferences import SpurLinePrefs

        prefs = SpurLinePrefs()
        current = prefs.get_port()

        port, ok = QtWidgets.QInputDialog.getInt(
            FreeCADGui.getMainWindow(),
            "SpurLine — Set port",
            "Localhost port for LightBurn / MillMage:",
            current,    # default
            1,          # min
            65535,      # max
        )

        if ok and port != current:
            prefs.set_port(port)
            FreeCAD.Console.PrintMessage(
                f"SpurLine: port set to {port} (secrets cleared).\n"
            )


FreeCADGui.addCommand("SpurLine_Port", SpurLine_Port())
