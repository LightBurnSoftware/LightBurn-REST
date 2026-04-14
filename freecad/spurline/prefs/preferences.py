"""
SpurLine — SpurLinePrefs

Thin wrapper around FreeCAD's built-in preference store
(``FreeCAD.ParamGet``).  Handles reading and writing the endpoint
strings for LightBurn and MillMage, and parsing them into their
component parts.

Endpoint string format:  https://<host>:<port>?secret=<secret>
e.g.                      https://192.168.1.50:8080?secret=YOUR_SECRET

The secret is the **shared secret** used to compute an HMAC-SHA256
Bearer token at send time — it is never sent directly as a header.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, parse_qs

import FreeCAD


# FreeCAD preferences group path for all SpurLine settings
_PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/SpurLine"


@dataclass
class EndpointConfig:
    """
    Parsed representation of a stored endpoint string.

    Attributes
    ----------
    url : str
        The base HTTPS URL including host and port,
        e.g. ``https://192.168.1.50:1234``
    token : str
        The shared secret used to compute the HMAC-SHA256 Bearer token.
        (Field kept as ``token`` to avoid cascading renames.)
    raw : str
        The original unparsed string as stored in preferences.
    """
    url:   str
    token: str
    raw:   str


class SpurLinePrefs:
    """
    Read/write SpurLine preferences via FreeCAD's built-in param store.

    All values are persisted across FreeCAD sessions automatically —
    no extra files or databases needed.
    """

    # Preference keys
    _KEY_LIGHTBURN = "LightBurnEndpoint"
    _KEY_MILLMAGE  = "MillMageEndpoint"

    def __init__(self):
        self._params = FreeCAD.ParamGet(_PARAM_PATH)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_endpoint(self, target: str) -> Optional[EndpointConfig]:
        """
        Return a parsed ``EndpointConfig`` for the given target, or
        ``None`` if no endpoint has been configured yet.

        Parameters
        ----------
        target : str
            ``'lightburn'`` or ``'millmage'``
        """
        raw = self.get_raw_endpoint(target)
        if not raw:
            return None
        return self._parse(raw)

    def get_raw_endpoint(self, target: str) -> str:
        """Return the raw endpoint string as stored, or ''."""
        key = self._key_for(target)
        return self._params.GetString(key, "")

    def set_endpoint(self, target: str, raw: str):
        """
        Persist the endpoint string for the given target.

        Parameters
        ----------
        target : str
            ``'lightburn'`` or ``'millmage'``
        raw : str
            Full endpoint string, e.g.
            ``https://192.168.1.50:8080?secret=YOUR_SECRET``
        """
        key = self._key_for(target)
        self._params.SetString(key, raw.strip())

    def clear_endpoint(self, target: str):
        """Remove the stored endpoint for the given target."""
        key = self._key_for(target)
        self._params.RemString(key)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _key_for(target: str) -> str:
        keys = {
            "lightburn": SpurLinePrefs._KEY_LIGHTBURN,
            "millmage":  SpurLinePrefs._KEY_MILLMAGE,
        }
        if target not in keys:
            raise ValueError(
                f"Unknown target {target!r}. Expected 'lightburn' or 'millmage'."
            )
        return keys[target]

    @staticmethod
    def _parse(raw: str) -> EndpointConfig:
        """
        Parse ``https://host:port?secret=VALUE`` into an ``EndpointConfig``.

        Raises
        ------
        ValueError
            If the string cannot be parsed into url + secret.
        """
        parsed = urlparse(raw)

        if parsed.scheme != "https":
            raise ValueError(
                f"Endpoint must start with https://  Got: {raw!r}"
            )

        qs = parse_qs(parsed.query)
        secrets = qs.get("secret", [])
        if not secrets or not secrets[0]:
            raise ValueError(
                f"Could not find 'secret' query parameter: {raw!r}\n"
                "Expected format: https://host:port?secret=VALUE"
            )

        secret = secrets[0]
        url = f"https://{parsed.hostname}:{parsed.port}"

        return EndpointConfig(url=url, token=secret, raw=raw)
