"""
SpurLine — SettingsDialog

Dialog for configuring LightBurn and MillMage endpoint URLs.
The shared secret is obtained automatically via /api/connect
when a send is attempted.
"""

try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets


class SettingsDialog(QtWidgets.QDialog):
    """Modal dialog for editing both endpoint URLs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SpurLine — Connection Settings")
        self.setMinimumWidth(480)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        info = QtWidgets.QLabel(
            "Enter the server URL for each target.\n"
            "SpurLine will request access automatically when you send.\n"
            "Example: https://localhost:8080"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # LightBurn
        lb_group = QtWidgets.QGroupBox("LightBurn")
        lb_layout = QtWidgets.QVBoxLayout(lb_group)
        self.w_lightburn = QtWidgets.QLineEdit()
        self.w_lightburn.setPlaceholderText("https://localhost:8080")
        lb_layout.addWidget(self.w_lightburn)
        layout.addWidget(lb_group)

        # MillMage
        mm_group = QtWidgets.QGroupBox("MillMage")
        mm_layout = QtWidgets.QVBoxLayout(mm_group)
        self.w_millmage = QtWidgets.QLineEdit()
        self.w_millmage.setPlaceholderText("https://localhost:8080")
        mm_layout.addWidget(self.w_millmage)
        layout.addWidget(mm_group)

        # Validation label
        self.lbl_error = QtWidgets.QLabel("")
        self.lbl_error.setStyleSheet("color: red;")
        layout.addWidget(self.lbl_error)

        # Buttons
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load(self):
        from freecad.spurline.prefs.preferences import SpurLinePrefs
        prefs = SpurLinePrefs()
        self.w_lightburn.setText(prefs.get_raw_endpoint("lightburn"))
        self.w_millmage.setText(prefs.get_raw_endpoint("millmage"))

    def _on_accept(self):
        from freecad.spurline.prefs.preferences import SpurLinePrefs

        lb_raw = self.w_lightburn.text().strip()
        mm_raw = self.w_millmage.text().strip()

        # Validate non-empty fields
        for label, raw in [("LightBurn", lb_raw), ("MillMage", mm_raw)]:
            if raw:
                err = self._validate(raw)
                if err:
                    self.lbl_error.setText(f"{label}: {err}")
                    return

        prefs = SpurLinePrefs()
        if lb_raw:
            prefs.set_endpoint("lightburn", lb_raw)
        else:
            prefs.clear_endpoint("lightburn")

        if mm_raw:
            prefs.set_endpoint("millmage", mm_raw)
        else:
            prefs.clear_endpoint("millmage")

        self.accept()

    @staticmethod
    def _validate(raw: str) -> str:
        """Return an error string if malformed, else ''."""
        if not raw.startswith("https://"):
            return "Must start with https://"
        return ""
