"""
SpurLine — FreeCAD workbench for generating 2D gear profiles
and sending them to LightBurn or MillMage over a local REST API.

FreeCAD loads this file automatically when it scans Mod/ directories.
It must register the workbench class and nothing else — keep it thin.
"""

import FreeCADGui


class SpurLineWorkbench(FreeCADGui.Workbench):
    """
    Top-level workbench descriptor.  FreeCAD instantiates this class and
    calls Initialize() the first time the user switches to SpurLine.
    Heavy imports (PySide2, freecad.gears, etc.) are deferred until
    Initialize() so FreeCAD startup time is not affected.
    """

    MenuText = "SpurLine"
    ToolTip  = "Generate 2D gear profiles and send to LightBurn / MillMage"
    # Icon path is relative to this file's directory
    Icon     = "resources/icons/spurline.svg"

    def Initialize(self):
        """
        Called once when the workbench is first activated.
        Register all commands and build the toolbar + menu.
        """
        from freecad.spurline.commands import (
            cmd_involute,
            cmd_rack,
            cmd_timing,
            cmd_extract,
            cmd_port,
            cmd_settings,
        )

        self._commands = [
            "SpurLine_Involute",
            "SpurLine_Rack",
            "SpurLine_Timing",
            "SpurLine_Extract",
        ]

        self.appendToolbar("SpurLine", self._commands)
        self.appendMenu("SpurLine", self._commands + ["Separator", "SpurLine_Port", "SpurLine_Settings"])

    def Activated(self):
        """Called every time the user switches into this workbench."""
        pass

    def Deactivated(self):
        """Called every time the user switches away from this workbench."""
        pass

    def ContextMenu(self, recipient):
        """
        Extend the right-click context menu when SpurLine is active.
        recipient is either 'view' or 'tree'.
        """
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(SpurLineWorkbench)
