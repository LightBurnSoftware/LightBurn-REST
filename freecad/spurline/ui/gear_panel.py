"""
SpurLine — GearPanel Qt task panel.

This is the main user-facing UI.  It is opened as a FreeCAD task panel
(left dock) by each of the three command classes.  It owns:

  - Parameter fields (teeth, module, bore, keyway, copies)
  - A live preview label showing computed pitch diameter
  - "Send to LightBurn" and "Send to MillMage" buttons
  - A "Preview in FreeCAD" button that creates the profile without sending

Layout
------
The form is a QWidget that FreeCAD embeds in its Task panel dock.
FreeCAD calls accept() when the user confirms and reject() on cancel.
We do NOT use the default OK/Cancel buttons — instead we swap them out
for the Send buttons below.  FreeCAD still calls accept()/reject()
internally; we just rename them to be context-appropriate.
"""

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtCore

import FreeCAD
import FreeCADGui


class GearPanel:
    """
    Task panel shown in FreeCAD's left Task dock.

    Parameters
    ----------
    gear_type : str
        One of 'involute', 'rack', 'timing'.
        Controls which parameter fields are shown/hidden.
    """

    # Belt profile choices shown when gear_type == 'timing'
    BELT_TYPES = ["gt2", "gt3", "gt5", "gt8", "htd3", "htd5", "htd8"]

    def __init__(self, gear_type: str):
        self.gear_type = gear_type
        self._last_face = None       # cached Part.Face from last preview
        self._preview_names = []     # doc object names from last preview

        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle(self._panel_title())
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _panel_title(self) -> str:
        return {
            "involute": "Involute Spur Gear",
            "rack":     "Involute Rack",
            "timing":   "Timing Belt Pulley",
        }.get(self.gear_type, "Gear Profile")

    def _build_ui(self):
        """Construct all widgets and lay them out."""
        layout = QtWidgets.QVBoxLayout(self.form)
        layout.setSpacing(8)

        # --- Parameter group box ---
        param_group = QtWidgets.QGroupBox("Parameters")
        param_form  = QtWidgets.QFormLayout(param_group)
        layout.addWidget(param_group)

        # Teeth (all gear types)
        self.w_teeth = QtWidgets.QSpinBox()
        self.w_teeth.setRange(6, 500)
        self.w_teeth.setValue(20)
        self.w_teeth.setToolTip("Number of teeth")
        param_form.addRow("Teeth:", self.w_teeth)

        # Module (involute + rack only)
        self.w_module = QtWidgets.QDoubleSpinBox()
        self.w_module.setRange(0.1, 50.0)
        self.w_module.setValue(2.0)
        self.w_module.setSingleStep(0.5)
        self.w_module.setDecimals(2)
        self.w_module.setSuffix(" mm")
        self.w_module.setToolTip("Gear module (pitch diameter / tooth count)")
        self._row_module = param_form.addRow("Module:", self.w_module)

        # Pressure angle (involute + rack only)
        self.w_pressure = QtWidgets.QDoubleSpinBox()
        self.w_pressure.setRange(10.0, 30.0)
        self.w_pressure.setValue(20.0)
        self.w_pressure.setSingleStep(0.5)
        self.w_pressure.setDecimals(1)
        self.w_pressure.setSuffix("°")
        self.w_pressure.setToolTip("Standard: 20°")
        self._row_pressure = param_form.addRow("Pressure angle:", self.w_pressure)

        # Belt type (timing only)
        self.w_belt = QtWidgets.QComboBox()
        self.w_belt.addItems(self.BELT_TYPES)
        self.w_belt.setToolTip("Belt profile standard")
        self._row_belt = param_form.addRow("Belt type:", self.w_belt)

        # Bore diameter (not rack)
        self.w_bore = QtWidgets.QDoubleSpinBox()
        self.w_bore.setRange(0.0, 200.0)
        self.w_bore.setValue(0.0)
        self.w_bore.setDecimals(2)
        self.w_bore.setSuffix(" mm")
        self.w_bore.setSpecialValueText("None")
        self.w_bore.setToolTip("Center bore diameter (0 = no bore)")
        self._row_bore = param_form.addRow("Bore diameter:", self.w_bore)

        # Keyway width (only active when bore > 0, not rack)
        self.w_keyway = QtWidgets.QDoubleSpinBox()
        self.w_keyway.setRange(0.0, 50.0)
        self.w_keyway.setValue(0.0)
        self.w_keyway.setDecimals(2)
        self.w_keyway.setSuffix(" mm")
        self.w_keyway.setSpecialValueText("None")
        self.w_keyway.setToolTip("Keyway width (0 = no keyway).  Requires bore > 0.")
        self._row_keyway = param_form.addRow("Keyway width:", self.w_keyway)

        # Copies
        self.w_copies = QtWidgets.QSpinBox()
        self.w_copies.setRange(1, 50)
        self.w_copies.setValue(1)
        self.w_copies.setToolTip("Number of copies to place on the output sheet")
        param_form.addRow("Copies:", self.w_copies)

        # --- Live info label ---
        self.lbl_info = QtWidgets.QLabel("")
        self.lbl_info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.lbl_info)

        # --- Preview button ---
        self.btn_preview = QtWidgets.QPushButton("Preview in FreeCAD")
        self.btn_preview.setToolTip(
            "Generate the profile in FreeCAD so you can inspect and measure it "
            "before sending.  Does not send anything."
        )
        layout.addWidget(self.btn_preview)

        # --- Send buttons ---
        send_group = QtWidgets.QGroupBox("Send to machine software")
        send_layout = QtWidgets.QHBoxLayout(send_group)
        layout.addWidget(send_group)

        self.btn_lightburn = QtWidgets.QPushButton("Send to LightBurn")
        self.btn_millmage  = QtWidgets.QPushButton("Send to MillMage")
        send_layout.addWidget(self.btn_lightburn)
        send_layout.addWidget(self.btn_millmage)

        # --- Wire signals ---
        self.w_teeth.valueChanged.connect(self._update_info)
        self.w_module.valueChanged.connect(self._update_info)
        self.w_bore.valueChanged.connect(self._on_bore_changed)

        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_lightburn.clicked.connect(self._on_send_lightburn)
        self.btn_millmage.clicked.connect(self._on_send_millmage)

        # --- Apply visibility rules for this gear type ---
        self._apply_gear_type_visibility()
        self._update_info()

    def _apply_gear_type_visibility(self):
        """Show/hide fields that don't apply to the current gear type."""
        is_timing = self.gear_type == "timing"
        is_rack   = self.gear_type == "rack"

        # Module + pressure angle hidden for timing pulleys
        self.w_module.setVisible(not is_timing)
        self.w_pressure.setVisible(not is_timing)
        # Belt type only shown for timing
        self.w_belt.setVisible(is_timing)
        # Bore + keyway hidden for racks (no center shaft)
        self.w_bore.setVisible(not is_rack)
        self.w_keyway.setVisible(not is_rack)

    # ------------------------------------------------------------------
    # Reactive UI helpers
    # ------------------------------------------------------------------

    def _update_info(self):
        """Recompute and display the pitch diameter whenever params change."""
        if self.gear_type in ("involute", "rack"):
            pitch_d = self.w_teeth.value() * self.w_module.value()
            self.lbl_info.setText(f"Pitch diameter: {pitch_d:.2f} mm")
        else:
            self.lbl_info.setText("")

    def _on_bore_changed(self, value: float):
        """Enable/disable keyway field based on whether bore is set."""
        has_bore = value > 0.0
        self.w_keyway.setEnabled(has_bore)
        if not has_bore:
            self.w_keyway.setValue(0.0)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _collect_params(self) -> dict:
        """Read all widget values into a plain dict."""
        return {
            "gear_type":   self.gear_type,
            "teeth":       self.w_teeth.value(),
            "module":      self.w_module.value(),
            "pressure":    self.w_pressure.value(),
            "belt_type":   self.w_belt.currentText(),
            "bore":        self.w_bore.value() or None,
            "keyway_w":    self.w_keyway.value() or None,
            "copies":      self.w_copies.value(),
        }

    def _on_preview(self):
        """
        Generate the 2D profile and add it to the FreeCAD document
        so the user can inspect / measure it.  Caches the result in
        self._last_face for reuse by the Send buttons.
        """
        from freecad.spurline.core.profile_extractor import ProfileExtractor
        from freecad.spurline.core.sheet_composer    import SheetComposer

        params = self._collect_params()
        try:
            self._remove_preview()

            extractor = ProfileExtractor()
            face = extractor.extract(params)
            self._last_face = face

            composer = SheetComposer()
            features = composer.place_in_document(face, params["copies"])
            self._preview_names = [f.Name for f in features]

            self.lbl_info.setText("Preview added to document.")
        except Exception as exc:
            FreeCAD.Console.PrintError(f"SpurLine preview error: {exc}\n")
            self.lbl_info.setText(f"Preview failed: {exc}")

    def _remove_preview(self):
        """Remove document objects from the previous preview."""
        doc = FreeCAD.ActiveDocument
        if doc is None:
            return
        for name in self._preview_names:
            try:
                doc.removeObject(name)
            except Exception:
                pass
        self._preview_names = []
        doc.recompute()

    def _on_send_lightburn(self):
        """Generate the profile (if needed) and POST it to LightBurn."""
        self._send(target="lightburn")

    def _on_send_millmage(self):
        """Generate the profile (if needed) and POST it to MillMage."""
        self._send(target="millmage")

    def _send(self, target: str):
        """
        Shared send logic.

        1. Extract profile (reuse cached face if available)
        2. Export to DXF bytes in memory
        3. Ensure we have a shared secret (auto-connect if needed)
        4. POST to the configured endpoint
        5. On auth error, reconnect and retry once
        """
        from freecad.spurline.core.profile_extractor import ProfileExtractor
        from freecad.spurline.core.sheet_composer    import SheetComposer
        from freecad.spurline.api.client             import SpurLineClient
        from freecad.spurline.prefs.preferences      import SpurLinePrefs

        params = self._collect_params()

        # --- Step 1: ensure we have a face ---
        if self._last_face is None:
            try:
                self._last_face = ProfileExtractor().extract(params)
            except Exception as exc:
                self._show_error("Profile generation failed", str(exc))
                return

        # --- Step 2: export to bytes ---
        try:
            composer  = SheetComposer()
            dxf_bytes = composer.to_dxf_bytes(self._last_face, params["copies"])
        except Exception as exc:
            self._show_error("Export failed", str(exc))
            return

        # --- Step 3: ensure connected ---
        prefs  = SpurLinePrefs()
        client = SpurLineClient()

        endpoint = self._ensure_connected(target, prefs, client)
        if endpoint is None:
            return

        # --- Step 4: send ---
        result = client.send(endpoint, dxf_bytes, fmt="dxf")

        if result.success:
            self.lbl_info.setText(f"File accepted by {target.title()} (importing...)")
        elif result.is_auth_error:
            # Secret may be stale — reconnect and retry once
            prefs.set_secret(target, "")
            endpoint = self._ensure_connected(target, prefs, client)
            if endpoint is None:
                return
            retry = client.send(endpoint, dxf_bytes, fmt="dxf")
            if retry.success:
                self.lbl_info.setText(f"File accepted by {target.title()} (importing...)")
            else:
                self._show_error(f"Could not reach {target.title()}", retry.error_message)
        else:
            self._show_error(
                f"Could not reach {target.title()}",
                result.error_message,
            )

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self, target, prefs, client):
        """
        Return an ``EndpointConfig`` with a valid secret, or ``None``
        if the connection could not be established.
        """
        endpoint = prefs.get_endpoint(target)

        if not endpoint.token:
            self.lbl_info.setText(f"Requesting access from {target.title()}...")
            self.form.repaint()  # show the status before blocking call
            result = client.connect(endpoint.url)
            if result.success:
                prefs.set_secret(target, result.secret)
                return prefs.get_endpoint(target)
            self._show_error("Connection failed", result.error_message)
            return None

        return endpoint

    # ------------------------------------------------------------------
    # Dialog helpers
    # ------------------------------------------------------------------

    def _show_error(self, title: str, message: str):
        """Show a modal error dialog."""
        QtWidgets.QMessageBox.critical(self.form, f"SpurLine — {title}", message)

    # ------------------------------------------------------------------
    # FreeCAD task panel protocol
    # ------------------------------------------------------------------

    def accept(self):
        """
        Called by FreeCAD when the user presses the panel's OK button.
        We don't use a generic OK here — the Send buttons handle
        acceptance — so this is a no-op that just closes the panel.
        """
        FreeCADGui.Control.closeDialog()

    def reject(self):
        """Called when the user presses Cancel or closes the dock."""
        FreeCADGui.Control.closeDialog()
