"""
SpurLine — SpurLinePrefs

Thin wrapper around FreeCAD's built-in preference store.
Stores the shared secrets obtained from LightBurn and MillMage
via the ``/api/connect`` pairing flow, and the localhost port.
"""

from __future__ import annotations
from dataclasses import dataclass

import FreeCAD


_PARAM_PATH  = "User parameter:BaseApp/Preferences/Mod/SpurLine"
_DEFAULT_PORT = 19522


@dataclass
class EndpointConfig:
    """
    Endpoint descriptor passed to the REST client.

    Attributes
    ----------
    url : str
        Base URL, e.g. ``http://localhost:19522``.
    token : str
        Shared secret for HMAC-SHA256 auth.  Empty if not yet authorized.
    """
    url:   str
    token: str


class SpurLinePrefs:
    """
    Read/write SpurLine preferences via FreeCAD's built-in param store.
    """

    _PORT_KEY    = "Port"
    _SECRET_KEYS = {
        "lightburn": "LightBurnSecret",
        "millmage":  "MillMageSecret",
    }

    def __init__(self):
        self._params = FreeCAD.ParamGet(_PARAM_PATH)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_endpoint(self, target: str) -> EndpointConfig:
        """
        Return the endpoint for the given target.

        Always succeeds.  The ``token`` field is empty if no secret
        has been obtained yet.
        """
        self._validate_target(target)
        secret = self._params.GetString(self._SECRET_KEYS[target], "")
        return EndpointConfig(url=self._base_url(), token=secret)

    def get_port(self) -> int:
        """Return the configured localhost port (default: 19522)."""
        return self._params.GetInt(self._PORT_KEY, _DEFAULT_PORT)

    def set_port(self, port: int):
        """
        Set the localhost port.  Clears stored secrets because a
        different port means a different server instance.
        """
        self._params.SetInt(self._PORT_KEY, port)
        self.clear_all_secrets()

    def set_secret(self, target: str, secret: str):
        """Store the shared secret obtained from ``/api/connect``."""
        self._validate_target(target)
        self._params.SetString(self._SECRET_KEYS[target], secret)

    def clear_all_secrets(self):
        """Remove all stored secrets (re-authorization will be required)."""
        for key in self._SECRET_KEYS.values():
            self._params.SetString(key, "")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _base_url(self) -> str:
        return f"http://localhost:{self.get_port()}"

    @staticmethod
    def _validate_target(target: str):
        if target not in ("lightburn", "millmage"):
            raise ValueError(
                f"Unknown target {target!r}. Expected 'lightburn' or 'millmage'."
            )
