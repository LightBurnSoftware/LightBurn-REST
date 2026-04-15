"""
SpurLine — TokenDialog

Shown when a REST call fails and the user needs to configure or
correct the endpoint URL for a specific target.

The shared secret is obtained automatically via /api/connect;
the user only needs to provide the server URL.
"""

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtCore


class TokenDialog(QtWidgets.QDialog):
    """
    Modal dialog for entering or correcting the endpoint URL
    for a specific target (lightburn or millmage).

    Parameters
    ----------
    target : str
        'lightburn' or 'millmage' — used to label the dialog and
        to know which preferences key to write.
    parent : QWidget, optional
    """

    def __init__(self, target: str, parent=None):
        super().__init__(parent)
        self.target = target
        self.setWindowTitle(f"SpurLine — Configure {target.title()} endpoint")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load_current()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # Explanation label
        info = QtWidgets.QLabel(
            f"Enter the server URL for {self.target.title()}.\n"
            "SpurLine will request access automatically when you send.\n"
            "Example: https://localhost:8080"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Endpoint input
        self.w_endpoint = QtWidgets.QLineEdit()
        self.w_endpoint.setPlaceholderText("https://localhost:8080")
        layout.addWidget(self.w_endpoint)

        # Validation feedback label (shown in red when format is wrong)
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

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _load_current(self):
        """Pre-fill the field with whatever is already stored."""
        from freecad.spurline.prefs.preferences import SpurLinePrefs
        current = SpurLinePrefs().get_raw_endpoint(self.target)
        if current:
            self.w_endpoint.setText(current)

    def _on_accept(self):
        """Validate format then save to preferences."""
        from freecad.spurline.prefs.preferences import SpurLinePrefs

        raw = self.w_endpoint.text().strip()
        error = self._validate(raw)
        if error:
            self.lbl_error.setText(error)
            return

        SpurLinePrefs().set_endpoint(self.target, raw)
        self.accept()

    @staticmethod
    def _validate(raw: str) -> str:
        """
        Return an error string if the endpoint is malformed, else ''.

        Expected format: https://<host>[:<port>]
        """
        if not raw:
            return "Endpoint URL cannot be empty."
        if not raw.startswith("https://"):
            return "Endpoint must start with https://"
        return ""
