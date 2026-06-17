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
# LightBurn and MillMage listen on different default ports.
_DEFAULT_PORTS = {"lightburn": 19520, "millmage": 19521}


@dataclass
class EndpointConfig:
    """
    Endpoint descriptor passed to the REST client.

    Attributes
    ----------
    url : str
        Base URL, e.g. ``http://localhost:19520``.
    token : str
        Shared secret for HMAC-SHA256 auth.  Empty if not yet authorized.
    """
    url:   str
    token: str


class SpurLinePrefs:
    """
    Read/write SpurLine preferences via FreeCAD's built-in param store.
    """

    _PORT_KEYS = {
        "lightburn": "LightBurnPort",
        "millmage":  "MillMagePort",
    }
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
        return EndpointConfig(url=self._base_url(target), token=secret)

    def get_port(self, target: str) -> int:
        """Return the configured port (defaults: LightBurn 19520, MillMage 19521)."""
        self._validate_target(target)
        return self._params.GetInt(self._PORT_KEYS[target], _DEFAULT_PORTS[target])

    def set_port(self, target: str, port: int):
        """
        Set the port for ``target``.  Clears that target's stored secret
        because a different port means a different server instance.
        """
        self._validate_target(target)
        self._params.SetInt(self._PORT_KEYS[target], port)
        self._params.SetString(self._SECRET_KEYS[target], "")

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

    def _base_url(self, target: str) -> str:
        return f"http://localhost:{self.get_port(target)}"

    @staticmethod
    def _validate_target(target: str):
        if target not in ("lightburn", "millmage"):
            raise ValueError(
                f"Unknown target {target!r}. Expected 'lightburn' or 'millmage'."
            )
