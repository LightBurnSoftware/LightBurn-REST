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
        self._plane_name = None  # cutting plane doc object name

        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Extract Profiles")

        self._items = []       # list of dicts with obj, spin, check
        self._build_ui()
        self._create_cutting_plane()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self.form)
        layout.setSpacing(8)

        # Shared controls (above tabs)
        self._build_object_list(layout)
        self._build_plane_group(layout)

        # --- Tabs ---
        self._tabs = QtWidgets.QTabWidget()
        layout.addWidget(self._tabs)

        # Tab 1: Single Slice
        single_tab = QtWidgets.QWidget()
        single_layout = QtWidgets.QVBoxLayout(single_tab)
        self._build_override_group(single_layout)

        self.lbl_info = QtWidgets.QLabel("")
        self.lbl_info.setAlignment(QtCore.Qt.AlignCenter)
        single_layout.addWidget(self.lbl_info)

        self.btn_preview = QtWidgets.QPushButton("Preview in FreeCAD")
        self.btn_preview.setToolTip(
            "Generate the 2D profile at the cutting plane position."
        )
        self.btn_preview.clicked.connect(self._on_preview)
        single_layout.addWidget(self.btn_preview)

        send_group = QtWidgets.QGroupBox("Send to machine software")
        send_layout = QtWidgets.QHBoxLayout(send_group)
        self.btn_lightburn = QtWidgets.QPushButton("Send to LightBurn")
        self.btn_millmage  = QtWidgets.QPushButton("Send to MillMage")
        send_layout.addWidget(self.btn_lightburn)
        send_layout.addWidget(self.btn_millmage)
        single_layout.addWidget(send_group)
        self.btn_lightburn.clicked.connect(self._on_send_lightburn)
        self.btn_millmage.clicked.connect(self._on_send_millmage)

        self._tabs.addTab(single_tab, "Single Slice")

        # Tab 2: Multi-Slice
        multi_tab = QtWidgets.QWidget()
        multi_layout = QtWidgets.QVBoxLayout(multi_tab)
        self._build_multi_slice_tab(multi_layout)
        self._tabs.addTab(multi_tab, "Multi-Slice")

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

    def _build_multi_slice_tab(self, parent_layout):
        """Build the multi-slice advanced controls."""
        form = QtWidgets.QFormLayout()
        parent_layout.addLayout(form)

        # Mode selector
        self.w_ms_mode = QtWidgets.QComboBox()
        self.w_ms_mode.addItems(["Fixed distance", "Slice count"])
        form.addRow("Mode:", self.w_ms_mode)

        # Value spinbox (meaning changes with mode)
        self.w_ms_value = QtWidgets.QDoubleSpinBox()
        self.w_ms_value.setRange(0.1, 500.0)
        self.w_ms_value.setValue(2.0)
        self.w_ms_value.setDecimals(2)
        self.w_ms_value.setSuffix(" mm")
        form.addRow("Interval:", self.w_ms_value)

        # Computed info
        self.lbl_ms_info = QtWidgets.QLabel("")
        self.lbl_ms_info.setAlignment(QtCore.Qt.AlignCenter)
        parent_layout.addWidget(self.lbl_ms_info)

        # Preview + send
        self.btn_ms_preview = QtWidgets.QPushButton("Preview All Slices")
        self.btn_ms_preview.clicked.connect(self._on_ms_preview)
        parent_layout.addWidget(self.btn_ms_preview)

        ms_send_group = QtWidgets.QGroupBox("Send all slices")
        ms_send_layout = QtWidgets.QHBoxLayout(ms_send_group)
        self.btn_ms_lightburn = QtWidgets.QPushButton("Send to LightBurn")
        self.btn_ms_millmage  = QtWidgets.QPushButton("Send to MillMage")
        ms_send_layout.addWidget(self.btn_ms_lightburn)
        ms_send_layout.addWidget(self.btn_ms_millmage)
        parent_layout.addWidget(ms_send_group)

        self.btn_ms_lightburn.clicked.connect(lambda: self._on_ms_send("lightburn"))
        self.btn_ms_millmage.clicked.connect(lambda: self._on_ms_send("millmage"))

        parent_layout.addStretch()

        # Wire mode changes
        self.w_ms_mode.currentIndexChanged.connect(self._on_ms_mode_changed)
        self.w_ms_value.valueChanged.connect(self._update_ms_info)
        self._on_ms_mode_changed()

    def _on_ms_mode_changed(self):
        """Update the value spinbox label and limits for the selected mode."""
        is_distance = self.w_ms_mode.currentIndex() == 0
        if is_distance:
            self.w_ms_value.setSuffix(" mm")
            self.w_ms_value.setRange(0.1, 500.0)
            self.w_ms_value.setDecimals(2)
            self.w_ms_value.setValue(2.0)
        else:
            self.w_ms_value.setSuffix(" slices")
            self.w_ms_value.setRange(2, 200)
            self.w_ms_value.setDecimals(0)
            self.w_ms_value.setValue(10)
        self._update_ms_info()

    def _update_ms_info(self):
        """Show the computed slice count / spacing."""
        extent = self._plane_hi - self._plane_lo
        if extent <= 0:
            self.lbl_ms_info.setText("")
            return

        is_distance = self.w_ms_mode.currentIndex() == 0
        if is_distance:
            spacing = self.w_ms_value.value()
            count = max(1, int(extent / spacing) + 1)
            self.lbl_ms_info.setText(f"{count} slices over {extent:.1f} mm")
        else:
            count = int(self.w_ms_value.value())
            spacing = extent / max(count - 1, 1)
            self.lbl_ms_info.setText(
                f"{count} slices at {spacing:.2f} mm intervals"
            )

    def _compute_ms_offsets(self):
        """Return a list of offset values along the active axis.

        The first and last offsets are inset by a small epsilon so
        the slice plane doesn't land exactly on a bounding-box face,
        which can produce zero wires due to floating-point tangency.
        """
        _EPS = 0.01  # mm inset from bounding box faces
        lo = self._plane_lo + _EPS
        hi = self._plane_hi - _EPS
        extent = hi - lo
        if extent <= 0:
            return [(self._plane_lo + self._plane_hi) / 2.0]

        is_distance = self.w_ms_mode.currentIndex() == 0
        if is_distance:
            spacing = self.w_ms_value.value()
            count = max(1, int(extent / spacing) + 1)
        else:
            count = int(self.w_ms_value.value())

        if count <= 1:
            return [(lo + hi) / 2.0]

        return [
            lo + i * extent / (count - 1)
            for i in range(count)
        ]

    def _placement_at_offset(self, offset):
        """Build a Placement for the current orientation at a given offset."""
        bb = getattr(self, "_bb", None)
        if bb is None:
            return None
        cx = (bb.XMin + bb.XMax) / 2.0
        cy = (bb.YMin + bb.YMax) / 2.0
        cz = (bb.ZMin + bb.ZMax) / 2.0

        orient = self._plane_orientation
        if orient == "top":
            pos = FreeCAD.Vector(cx, cy, offset)
            rot = FreeCAD.Rotation(0, 0, 0)
        elif orient == "front":
            pos = FreeCAD.Vector(cx, offset, cz)
            rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 90)
        else:
            pos = FreeCAD.Vector(offset, cy, cz)
            rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), -90)
        return FreeCAD.Placement(pos, rot)

    def _on_ms_preview(self):
        """Preview all slices in the document."""
        from freecad.spurline.core.selection_extractor import SelectionExtractor
        from freecad.spurline.core.sheet_composer import SheetComposer

        items = self._collect_items()
        if not items:
            self.lbl_ms_info.setText("No objects selected.")
            return

        bore, keyway_w = self._get_overrides()
        offsets = self._compute_ms_offsets()
        extractor = SelectionExtractor()

        try:
            self._remove_preview()
            face_items = []
            for offset in offsets:
                placement = self._placement_at_offset(offset)
                for obj, copies in items:
                    face = extractor.extract_face(
                        obj, bore=bore, keyway_w=keyway_w, placement=placement,
                    )
                    face_items.append((face, copies))

            composer = SheetComposer()
            features = composer.place_multi_in_document(face_items)
            self._preview_names = [f.Name for f in features]

            self.lbl_ms_info.setText(
                f"Preview: {len(offsets)} slices, "
                f"{len(face_items)} total profiles."
            )
        except Exception as exc:
            FreeCAD.Console.PrintError(f"SpurLine multi-slice error: {exc}\n")
            self.lbl_ms_info.setText(f"Failed: {exc}")

    def _on_ms_send(self, target: str):
        """Send each slice as a separate DXF upload."""
        from freecad.spurline.core.selection_extractor import SelectionExtractor
        from freecad.spurline.core.sheet_composer import SheetComposer
        from freecad.spurline.api.client import SpurLineClient
        from freecad.spurline.prefs.preferences import SpurLinePrefs

        items = self._collect_items()
        if not items:
            self.lbl_ms_info.setText("No objects selected.")
            return

        prefs = SpurLinePrefs()
        client = SpurLineClient()
        endpoint = self._ensure_connected(target, prefs, client)
        if endpoint is None:
            return

        bore, keyway_w = self._get_overrides()
        offsets = self._compute_ms_offsets()
        extractor = SelectionExtractor()
        composer = SheetComposer()

        bar = FreeCAD.Base.ProgressIndicator()
        bar.start(f"Sending {len(offsets)} slices to {target.title()}...", 0)

        sent = 0
        try:
            for i, offset in enumerate(offsets):
                self.lbl_ms_info.setText(
                    f"Slice {i + 1}/{len(offsets)}: extracting..."
                )
                self.form.repaint()

                placement = self._placement_at_offset(offset)
                face_items = []
                for obj, copies in items:
                    face = extractor.extract_face(
                        obj, bore=bore, keyway_w=keyway_w, placement=placement,
                    )
                    face_items.append((face, copies))

                dxf_bytes = composer.multi_to_dxf_bytes(face_items)

                self.lbl_ms_info.setText(
                    f"Slice {i + 1}/{len(offsets)}: uploading..."
                )
                self.form.repaint()

                result = client.send(endpoint, dxf_bytes, fmt="dxf")
                if not result.success:
                    self._show_error(
                        f"Slice {i + 1} failed",
                        result.error_message,
                    )
                    break
                sent += 1

            self.lbl_ms_info.setText(
                f"{sent}/{len(offsets)} slices sent to {target.title()}."
            )
        except Exception as exc:
            self._show_error("Multi-slice failed", str(exc))
        finally:
            bar.stop()

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

    def _build_plane_group(self, parent_layout):
        """Build the cutting plane position and orientation controls."""
        group = QtWidgets.QGroupBox("Cutting Plane")
        vbox = QtWidgets.QVBoxLayout(group)
        parent_layout.addWidget(group)

        # Orientation presets
        orient_layout = QtWidgets.QHBoxLayout()
        orient_layout.addWidget(QtWidgets.QLabel("View:"))
        self.btn_top   = QtWidgets.QPushButton("Top")
        self.btn_front = QtWidgets.QPushButton("Front")
        self.btn_right = QtWidgets.QPushButton("Right")
        orient_layout.addWidget(self.btn_top)
        orient_layout.addWidget(self.btn_front)
        orient_layout.addWidget(self.btn_right)
        vbox.addLayout(orient_layout)

        # Offset slider + value label
        slider_layout = QtWidgets.QHBoxLayout()
        slider_layout.addWidget(QtWidgets.QLabel("Offset:"))
        self.w_plane_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.w_plane_slider.setRange(0, 1000)
        self.w_plane_slider.setValue(500)
        slider_layout.addWidget(self.w_plane_slider, 1)
        self.lbl_plane_value = QtWidgets.QLabel("0.00 mm")
        self.lbl_plane_value.setMinimumWidth(60)
        slider_layout.addWidget(self.lbl_plane_value)
        vbox.addLayout(slider_layout)

        # Wire signals
        self.btn_top.clicked.connect(lambda: self._set_plane_orientation("top"))
        self.btn_front.clicked.connect(lambda: self._set_plane_orientation("front"))
        self.btn_right.clicked.connect(lambda: self._set_plane_orientation("right"))
        self.w_plane_slider.valueChanged.connect(self._on_plane_slider_changed)

        # Internal state
        self._plane_orientation = "top"
        self._plane_lo = 0.0
        self._plane_hi = 1.0

    # ------------------------------------------------------------------
    # Reactive UI helpers
    # ------------------------------------------------------------------

    def _on_bore_changed(self, value: float):
        has_bore = value > 0.0
        self.w_keyway.setEnabled(has_bore)
        if not has_bore:
            self.w_keyway.setValue(0.0)

    # ------------------------------------------------------------------
    # Cutting plane
    # ------------------------------------------------------------------

    def _compute_bounding_box(self):
        """Compute the combined bounding box in global coordinates."""
        from freecad.spurline.core.selection_extractor import SelectionExtractor
        bb = None
        for obj in self._selection:
            if not SelectionExtractor.has_shape(obj):
                continue
            obb = SelectionExtractor._global_shape(obj).BoundBox
            if bb is None:
                bb = FreeCAD.BoundBox(obb)
            else:
                bb.add(obb)
        return bb

    def _create_cutting_plane(self):
        """Create a visible cutting plane in the document."""
        import Part as _Part

        doc = FreeCAD.ActiveDocument
        if doc is None:
            return

        bb = self._compute_bounding_box()
        if bb is None:
            return

        self._bb = bb
        self._plane_size = max(bb.XLength, bb.YLength, bb.ZLength) * 1.2
        if self._plane_size < 10.0:
            self._plane_size = 10.0

        # Create a flat centered square at the origin — Placement
        # will position and orient it.
        half = self._plane_size / 2.0
        plane_shape = _Part.makePlane(
            self._plane_size, self._plane_size,
            FreeCAD.Vector(-half, -half, 0),
        )

        plane_obj = doc.addObject("Part::Feature", "SpurLine_CuttingPlane")
        plane_obj.Shape = plane_shape
        self._plane_name = plane_obj.Name

        # Semi-transparent blue
        if hasattr(plane_obj, "ViewObject") and plane_obj.ViewObject:
            plane_obj.ViewObject.Transparency = 70
            plane_obj.ViewObject.ShapeColor = (0.2, 0.5, 1.0)

        # Set default orientation (top) and offset (midpoint)
        self._set_plane_orientation("top")

        FreeCADGui.SendMsgToActiveView("ViewFit")

    def _set_plane_orientation(self, orient: str):
        """Switch the cutting plane to a preset orientation."""
        bb = getattr(self, "_bb", None)
        if bb is None:
            return

        self._plane_orientation = orient
        self._last_items = None  # invalidate cached extraction

        # Offset range depends on which axis the plane slides along
        if orient == "top":
            self._plane_lo, self._plane_hi = bb.ZMin, bb.ZMax
        elif orient == "front":
            self._plane_lo, self._plane_hi = bb.YMin, bb.YMax
        else:  # right
            self._plane_lo, self._plane_hi = bb.XMin, bb.XMax

        # Reset slider to midpoint
        self.w_plane_slider.blockSignals(True)
        self.w_plane_slider.setValue(500)  # midpoint of 0–1000
        self.w_plane_slider.blockSignals(False)

        self._update_plane_placement()
        if hasattr(self, "lbl_ms_info"):
            self._update_ms_info()

    def _on_plane_slider_changed(self, _value):
        """Called when the offset slider changes."""
        self._last_items = None
        self._update_plane_placement()

    def _slider_to_offset(self) -> float:
        """Map the slider's 0–1000 int to the actual mm offset."""
        t = self.w_plane_slider.value() / 1000.0
        return self._plane_lo + t * (self._plane_hi - self._plane_lo)

    def _update_plane_placement(self):
        """Reposition the plane from the current orientation + slider."""
        doc = FreeCAD.ActiveDocument
        if doc is None or not self._plane_name:
            return
        plane_obj = doc.getObject(self._plane_name)
        if plane_obj is None:
            return

        bb = getattr(self, "_bb", None)
        if bb is None:
            return

        cx = (bb.XMin + bb.XMax) / 2.0
        cy = (bb.YMin + bb.YMax) / 2.0
        cz = (bb.ZMin + bb.ZMax) / 2.0
        offset = self._slider_to_offset()

        orient = self._plane_orientation

        if orient == "top":
            pos = FreeCAD.Vector(cx, cy, offset)
            rot = FreeCAD.Rotation(0, 0, 0)           # identity — XY plane
        elif orient == "front":
            pos = FreeCAD.Vector(cx, offset, cz)
            rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 90)  # tilt to XZ
        else:  # right
            pos = FreeCAD.Vector(offset, cy, cz)
            rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), -90)  # tilt to YZ

        plane_obj.Placement = FreeCAD.Placement(pos, rot)
        doc.recompute()

        # Update the value label
        self.lbl_plane_value.setText(f"{offset:.2f} mm")

    def _get_plane_placement(self):
        """Read the cutting plane's current Placement, or None."""
        if not self._plane_name:
            return None
        doc = FreeCAD.ActiveDocument
        if doc is None:
            return None
        try:
            plane_obj = doc.getObject(self._plane_name)
            if plane_obj:
                return plane_obj.Placement
        except Exception:
            pass
        return None

    def _remove_cutting_plane(self):
        """Remove the cutting plane from the document."""
        if not self._plane_name:
            return
        doc = FreeCAD.ActiveDocument
        if doc is None:
            return
        try:
            doc.removeObject(self._plane_name)
        except Exception:
            pass
        self._plane_name = None

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
        placement = self._get_plane_placement()
        extractor = SelectionExtractor()

        try:
            self._remove_preview()
            face_items = []
            for obj, copies in items:
                face = extractor.extract_face(
                    obj, bore=bore, keyway_w=keyway_w, placement=placement,
                )
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

        bar = FreeCAD.Base.ProgressIndicator()
        bar.start(f"Sending to {target.title()}...", 0)

        try:
            # --- Step 1: ensure we have extracted faces ---
            if self._last_items is None:
                items = self._collect_items()
                if not items:
                    self._show_error("Nothing to send", "No objects are selected.")
                    return

                self.lbl_info.setText("Extracting profiles...")
                self.form.repaint()
                bore, keyway_w = self._get_overrides()
                placement = self._get_plane_placement()
                extractor = SelectionExtractor()
                try:
                    self._last_items = [
                        (extractor.extract_face(
                            obj, bore=bore, keyway_w=keyway_w, placement=placement,
                        ), copies)
                        for obj, copies in items
                    ]
                except Exception as exc:
                    self._show_error("Profile extraction failed", str(exc))
                    return

            # --- Step 2: export to DXF bytes ---
            self.lbl_info.setText("Exporting DXF...")
            self.form.repaint()
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
            self.lbl_info.setText(f"Uploading to {target.title()}...")
            self.form.repaint()
            result = client.send(endpoint, dxf_bytes, fmt="dxf")

            if result.success:
                self.lbl_info.setText(f"File accepted by {target.title()} (importing...)")
            elif result.is_auth_error:
                self._show_error(
                    "Authentication failed",
                    f"The stored secret was rejected by {target.title()}.\n\n"
                    "Use SpurLine > Reset authorizations from the menu,\n"
                    "then try sending again.",
                )
            else:
                self._show_error(
                    f"Could not reach {target.title()}",
                    result.error_message,
                )
        finally:
            bar.stop()

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
        self._remove_cutting_plane()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        self._remove_preview()
        self._remove_cutting_plane()
        FreeCADGui.Control.closeDialog()
