"""
SpurLine — SpurLineClient

Handles the HTTP POST to LightBurn or MillMage.

Responsibilities
----------------
- Build the request from an EndpointConfig + file bytes
- Compute an HMAC-SHA256 time-based Bearer token from the shared secret
- Return a SendResult describing success or the category of failure
- Never raise — all exceptions are caught and returned as SendResult

Two error categories, as specified:
  1. Connection / timeout — the listener is not running or unreachable
  2. Auth failure        — HTTP 401 / 403, token is wrong or missing

We use Python's stdlib ``urllib`` to avoid adding external dependencies.
``requests`` can be swapped in trivially if preferred.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.request
import urllib.error
import ssl
from dataclasses import dataclass
from typing import Optional

from freecad.spurline.prefs.preferences import EndpointConfig


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class SendResult:
    """
    Outcome of a single REST send attempt.

    Attributes
    ----------
    success : bool
    is_auth_error : bool
        True when the server responded with HTTP 401 or 403.
    error_message : str
        Human-readable explanation, empty on success.
    http_status : int or None
        The HTTP response code if a response was received.
    """
    success:         bool          = False
    is_auth_error:   bool          = False
    error_message:   str           = ""
    http_status:     Optional[int] = None
    server_filename: str           = ""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class SpurLineClient:
    """
    Stateless HTTP client.  Instantiate, call ``send()``, discard.
    """

    _ENDPOINT_PATH = "/api/file/upload"
    _CONTENT_TYPE  = "application/octet-stream"
    _TIMEOUT_SECONDS = 10

    def send(
        self,
        endpoint: Optional[EndpointConfig],
        file_bytes: bytes,
        fmt: str = "dxf",
    ) -> SendResult:
        """
        POST ``file_bytes`` to the endpoint described by ``endpoint``.

        Parameters
        ----------
        endpoint : EndpointConfig or None
            If None, returns an auth error prompting configuration.
        file_bytes : bytes
            Raw DXF or SVG content to POST.
        fmt : str
            ``'dxf'`` or ``'svg'`` — used to set the filename hint in
            the request (exact mechanism TBD from OpenAPI spec).

        Returns
        -------
        SendResult
        """
        if endpoint is None:
            return SendResult(
                success=False,
                is_auth_error=True,
                error_message="No endpoint configured for this target.",
            )

        url = f"{endpoint.url}{self._ENDPOINT_PATH}"

        try:
            result = self._do_post(url, endpoint.token, file_bytes, fmt)
        except urllib.error.HTTPError as exc:
            return self._handle_http_error(exc)
        except urllib.error.URLError as exc:
            return self._handle_url_error(exc)
        except Exception as exc:
            return SendResult(
                success=False,
                error_message=f"Unexpected error: {exc}",
            )

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_bearer_token(secret: str) -> str:
        """
        Compute the HMAC-SHA256 time-based Bearer token.

        The server accepts tokens for the current minute and the previous
        minute to handle clock drift.
        """
        message = str(int(time.time()) // 60).encode()
        return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    def _do_post(
        self,
        url: str,
        secret: str,
        body: bytes,
        fmt: str,
    ) -> SendResult:
        """Perform the actual HTTP POST and return a SendResult."""
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode    = ssl.CERT_NONE

        bearer = self._compute_bearer_token(secret)

        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type":  self._CONTENT_TYPE,
            "X-Filename":    f"gear.{fmt}",
        }

        req = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(
            req,
            timeout=self._TIMEOUT_SECONDS,
            context=ssl_ctx,
        ) as response:
            http_status = response.status
            if http_status == 202:
                resp_body = json.loads(response.read())
                return SendResult(
                    success=True,
                    http_status=http_status,
                    server_filename=resp_body.get("filename", ""),
                )
            return SendResult(success=True, http_status=http_status)

    @staticmethod
    def _handle_http_error(exc: urllib.error.HTTPError) -> SendResult:
        """Map HTTP error codes to SendResult categories."""
        status = exc.code
        if status in (401, 403):
            return SendResult(
                success=False,
                is_auth_error=True,
                http_status=status,
                error_message=(
                    f"Authentication failed (HTTP {status}).  "
                    "Please check your shared secret."
                ),
            )
        return SendResult(
            success=False,
            http_status=status,
            error_message=f"Server returned HTTP {status}: {exc.reason}",
        )

    @staticmethod
    def _handle_url_error(exc: urllib.error.URLError) -> SendResult:
        """Map connection/timeout errors to a user-friendly message."""
        reason = str(exc.reason)
        if "timed out" in reason.lower():
            msg = (
                "Connection timed out.  "
                "Make sure the REST listener is enabled in LightBurn / MillMage "
                "and that the host and port are correct."
            )
        elif "refused" in reason.lower():
            msg = (
                "Connection refused.  "
                "The REST listener does not appear to be running.  "
                "Enable it in LightBurn / MillMage settings."
            )
        else:
            msg = (
                f"Could not connect: {reason}\n"
                "Check that the host IP and port are correct and that "
                "the REST listener is enabled."
            )
        return SendResult(success=False, error_message=msg)
