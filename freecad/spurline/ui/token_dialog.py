"""
SpurLine — TokenDialog

Shown when a REST call returns an auth error, or when the user
wants to configure their endpoint string from scratch.

The endpoint string format is:  https://<host>:<port>?secret=<secret>
e.g.  https://192.168.1.50:8080?secret=YOUR_SECRET

The URL is obtained by scanning the QR code displayed in LightBurn
or MillMage after enabling the REST listener.  We store the full raw
string in preferences and parse it at send time.
"""

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtCore


class TokenDialog(QtWidgets.QDialog):
    """
    Modal dialog for entering or correcting the endpoint configuration
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
            f"Enter the endpoint URL for {self.target.title()}.\n"
            "Paste the URL from the QR code shown in the app.\n"
            "Example: https://192.168.1.50:8080?secret=YOUR_SECRET"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Endpoint input
        self.w_endpoint = QtWidgets.QLineEdit()
        self.w_endpoint.setPlaceholderText("https://172.16.0.100:8080?secret=...")
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

        Expected format: https://<host>:<port>?secret=<value>
        """
        if not raw:
            return "Endpoint string cannot be empty."
        if not raw.startswith("https://"):
            return "Endpoint must start with https://"
        if "?secret=" not in raw and "&secret=" not in raw:
            return "Missing ?secret= parameter.  Paste the full URL from the QR code."
        return ""
