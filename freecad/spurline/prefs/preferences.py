"""
SpurLine — SpurLinePrefs

Thin wrapper around FreeCAD's built-in preference store.
Stores the shared secrets obtained from LightBurn and MillMage
via the ``/api/connect`` pairing flow.

The server URL is fixed at ``https://localhost:8080``.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, parse_qs

import FreeCAD


_PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/SpurLine"
_BASE_URL   = "https://localhost:8080"


@dataclass
class EndpointConfig:
    """
    Endpoint descriptor passed to the REST client.

    Attributes
    ----------
    url : str
        Base HTTPS URL (always ``https://localhost:8080``).
    token : str
        Shared secret for HMAC-SHA256 auth.  Empty if not yet authorized.
    """
    url:   str
    token: str


class SpurLinePrefs:
    """
    Read/write SpurLine preferences via FreeCAD's built-in param store.
    """

    _SECRET_KEYS = {
        "lightburn": "LightBurnSecret",
        "millmage":  "MillMageSecret",
    }

    # Legacy keys from earlier versions (URL + secret combined)
    _OLD_KEYS = {
        "lightburn": "LightBurnEndpoint",
        "millmage":  "MillMageEndpoint",
    }
    _OLD_URL_KEYS = {
        "lightburn": "LightBurnUrl",
        "millmage":  "MillMageUrl",
    }

    def __init__(self):
        self._params = FreeCAD.ParamGet(_PARAM_PATH)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_endpoint(self, target: str) -> EndpointConfig:
        """
        Return the endpoint for the given target.

        Always succeeds — the URL is fixed.  The ``token`` field is
        empty if no secret has been obtained yet.
        """
        self._validate_target(target)
        self._maybe_migrate(target)
        secret = self._params.GetString(self._SECRET_KEYS[target], "")
        return EndpointConfig(url=_BASE_URL, token=secret)

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

    @staticmethod
    def _validate_target(target: str):
        if target not in ("lightburn", "millmage"):
            raise ValueError(
                f"Unknown target {target!r}. Expected 'lightburn' or 'millmage'."
            )

    def _maybe_migrate(self, target: str):
        """
        One-time migration: pull the secret out of any legacy keys
        and clean them up.
        """
        # Legacy combined format: https://host:port?secret=VALUE
        old_key = self._OLD_KEYS[target]
        old_raw = self._params.GetString(old_key, "")
        if old_raw:
            try:
                qs = parse_qs(urlparse(old_raw).query)
                secrets = qs.get("secret", [])
                if secrets and secrets[0]:
                    self._params.SetString(self._SECRET_KEYS[target], secrets[0])
            except Exception:
                pass
            self._params.RemString(old_key)

        # Legacy separate-URL key (no longer needed)
        old_url_key = self._OLD_URL_KEYS[target]
        if self._params.GetString(old_url_key, ""):
            self._params.RemString(old_url_key)
