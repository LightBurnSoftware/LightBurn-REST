"""
SpurLine — ExtractPanel Qt task panel.

Shown when the user selects existing objects in the document and clicks
"Extract Profile from Selection".  Lists the selected objects with
per-item copy counts, optional bore/keyway override, and the same
Preview / Send buttons as GearPanel.
"""

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtCore

import FreeCAD
import FreeCADGui


class ExtractPanel:
    """
    Task panel for extracting 2D profiles from selected document objects.

    Parameters
    ----------
    selection : list of App.DocumentObject
        Objects selected when the command was invoked.
    """

    def __init__(self, selection):
        self._selection = selection
        self._preview_names = []
        self._last_items = None  # cached list of (face, copies)

        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Extract Profiles")

        self._items = []       # list of dicts with obj, spin, check
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self.form)
        layout.setSpacing(8)

        self._build_object_list(layout)
        self._build_override_group(layout)

        # --- Info label ---
        self.lbl_info = QtWidgets.QLabel("")
        self.lbl_info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.lbl_info)

        # --- Preview button ---
        self.btn_preview = QtWidgets.QPushButton("Preview in FreeCAD")
        self.btn_preview.setToolTip(
            "Generate the 2D profiles in FreeCAD so you can inspect them "
            "before sending.  Does not send anything."
        )
        self.btn_preview.clicked.connect(self._on_preview)
        layout.addWidget(self.btn_preview)

        # --- Send buttons ---
        send_group = QtWidgets.QGroupBox("Send to machine software")
        send_layout = QtWidgets.QHBoxLayout(send_group)
        layout.addWidget(send_group)

        self.btn_lightburn = QtWidgets.QPushButton("Send to LightBurn")
        self.btn_millmage  = QtWidgets.QPushButton("Send to MillMage")
        send_layout.addWidget(self.btn_lightburn)
        send_layout.addWidget(self.btn_millmage)

        self.btn_lightburn.clicked.connect(self._on_send_lightburn)
        self.btn_millmage.clicked.connect(self._on_send_millmage)

    def _build_object_list(self, parent_layout):
        """Build the QTreeWidget listing selected objects."""
        from freecad.spurline.core.selection_extractor import SelectionExtractor

        group = QtWidgets.QGroupBox("Selected Objects")
        group_layout = QtWidgets.QVBoxLayout(group)
        parent_layout.addWidget(group)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["", "Label", "Type", "Size", "Copies"])
        self.tree.setRootIsDecorated(False)
        self.tree.setColumnWidth(0, 30)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 130)
        self.tree.setColumnWidth(3, 100)
        self.tree.setColumnWidth(4, 60)
        group_layout.addWidget(self.tree)

        for obj in self._selection:
            if not SelectionExtractor.has_shape(obj):
                continue

            item = QtWidgets.QTreeWidgetItem()
            item.setCheckState(0, QtCore.Qt.Checked)
            item.setText(1, obj.Label)
            item.setText(2, SelectionExtractor.get_type_info(obj))
            item.setText(3, SelectionExtractor.get_size_info(obj))
            self.tree.addTopLevelItem(item)

            spin = QtWidgets.QSpinBox()
            spin.setRange(1, 50)
            spin.setValue(1)
            self.tree.setItemWidget(item, 4, spin)

            self._items.append({
                "obj": obj,
                "tree_item": item,
                "spin": spin,
            })

        if not self._items:
            lbl = QtWidgets.QLabel("No objects with geometry found in selection.")
            group_layout.addWidget(lbl)

    def _build_override_group(self, parent_layout):
        """Build the optional bore / keyway override fields."""
        group = QtWidgets.QGroupBox("Bore / Keyway Override")
        form = QtWidgets.QFormLayout(group)
        parent_layout.addWidget(group)

        self.w_bore = QtWidgets.QDoubleSpinBox()
        self.w_bore.setRange(0.0, 200.0)
        self.w_bore.setValue(0.0)
        self.w_bore.setDecimals(2)
        self.w_bore.setSuffix(" mm")
        self.w_bore.setSpecialValueText("None")
        self.w_bore.setToolTip("Center bore diameter (0 = no override)")
        form.addRow("Bore diameter:", self.w_bore)

        self.w_keyway = QtWidgets.QDoubleSpinBox()
        self.w_keyway.setRange(0.0, 50.0)
        self.w_keyway.setValue(0.0)
        self.w_keyway.setDecimals(2)
        self.w_keyway.setSuffix(" mm")
        self.w_keyway.setSpecialValueText("None")
        self.w_keyway.setToolTip("Keyway width (0 = no override).  Requires bore > 0.")
        form.addRow("Keyway width:", self.w_keyway)

        self.w_bore.valueChanged.connect(self._on_bore_changed)

    # ------------------------------------------------------------------
    # Reactive UI helpers
    # ------------------------------------------------------------------

    def _on_bore_changed(self, value: float):
        has_bore = value > 0.0
        self.w_keyway.setEnabled(has_bore)
        if not has_bore:
            self.w_keyway.setValue(0.0)

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    def _collect_items(self):
        """
        Read the tree widget state and return a list of
        (obj, copies) for checked items.
        """
        result = []
        for entry in self._items:
            ti = entry["tree_item"]
            if ti.checkState(0) == QtCore.Qt.Checked:
                copies = entry["spin"].value()
                result.append((entry["obj"], copies))
        return result

    def _get_overrides(self):
        """Return (bore, keyway_w) from the override fields, or None."""
        bore = self.w_bore.value() or None
        keyway_w = self.w_keyway.value() or None
        return bore, keyway_w

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_preview(self):
        from freecad.spurline.core.selection_extractor import SelectionExtractor
        from freecad.spurline.core.sheet_composer import SheetComposer

        items = self._collect_items()
        if not items:
            self.lbl_info.setText("No objects selected.")
            return

        bore, keyway_w = self._get_overrides()
        extractor = SelectionExtractor()

        try:
            self._remove_preview()
            face_items = []
            for obj, copies in items:
                face = extractor.extract_face(obj, bore=bore, keyway_w=keyway_w)
                face_items.append((face, copies))

            self._last_items = face_items

            composer = SheetComposer()
            features = composer.place_multi_in_document(face_items)
            self._preview_names = [f.Name for f in features]

            total = sum(c for _, c in items)
            self.lbl_info.setText(
                f"Preview: {len(items)} profile(s), {total} total copies."
            )
        except Exception as exc:
            FreeCAD.Console.PrintError(f"SpurLine extract error: {exc}\n")
            self.lbl_info.setText(f"Extract failed: {exc}")

    def _remove_preview(self):
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
        self._send(target="lightburn")

    def _on_send_millmage(self):
        self._send(target="millmage")

    def _send(self, target: str):
        from freecad.spurline.core.selection_extractor import SelectionExtractor
        from freecad.spurline.core.sheet_composer import SheetComposer
        from freecad.spurline.api.client import SpurLineClient
        from freecad.spurline.prefs.preferences import SpurLinePrefs

        # --- Step 1: ensure we have extracted faces ---
        if self._last_items is None:
            items = self._collect_items()
            if not items:
                self._show_error("Nothing to send", "No objects are selected.")
                return

            bore, keyway_w = self._get_overrides()
            extractor = SelectionExtractor()
            try:
                self._last_items = [
                    (extractor.extract_face(obj, bore=bore, keyway_w=keyway_w), copies)
                    for obj, copies in items
                ]
            except Exception as exc:
                self._show_error("Profile extraction failed", str(exc))
                return

        # --- Step 2: export to DXF bytes ---
        try:
            composer = SheetComposer()
            dxf_bytes = composer.multi_to_dxf_bytes(self._last_items)
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
            self.form.repaint()
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
        QtWidgets.QMessageBox.critical(self.form, f"SpurLine — {title}", message)

    # ------------------------------------------------------------------
    # FreeCAD task panel protocol
    # ------------------------------------------------------------------

    def accept(self):
        self._remove_preview()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        self._remove_preview()
        FreeCADGui.Control.closeDialog()
