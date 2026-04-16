"""
SpurLine — SpurLineClient

Handles HTTP communication with LightBurn or MillMage.

Responsibilities
----------------
- Obtain a shared secret via ``POST /api/connect`` (local app pairing)
- POST file uploads to ``/api/file/upload``
- Compute an HMAC-SHA256 time-based Bearer token from the shared secret
- Return result objects describing success or failure category
- Never raise — all exceptions are caught and returned in results

We use Python's stdlib ``urllib`` to avoid adding external dependencies.
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
# Application identity
# ---------------------------------------------------------------------------

APPLICATION_NAME = "FreeCAD (SpurLine)"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ConnectResult:
    """
    Outcome of a ``POST /api/connect`` pairing attempt.

    Attributes
    ----------
    success : bool
    secret : str
        The shared secret returned by the server on approval.
    error_message : str
        Human-readable explanation, empty on success.
    """
    success:       bool = False
    secret:        str  = ""
    error_message: str  = ""


@dataclass
class SendResult:
    """
    Outcome of a single REST file-upload attempt.

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
    Stateless HTTP client.  Instantiate, call methods, discard.
    """

    _CONNECT_PATH    = "/api/connect"
    _UPLOAD_PATH     = "/api/file/upload"
    _CONTENT_TYPE    = "application/octet-stream"
    _TIMEOUT_SECONDS = 10
    _CONNECT_TIMEOUT = 35   # 30 s server consent dialog + 5 s buffer

    # ------------------------------------------------------------------
    # Connect (obtain shared secret)
    # ------------------------------------------------------------------

    def connect(self, base_url: str) -> ConnectResult:
        """
        Request a shared secret via ``POST /api/connect``.

        The server shows a consent dialog to the user with the
        application name.  If approved the secret is returned;
        if declined or timed out the server responds with 403.

        Previously approved applications receive their existing
        secret without re-prompting.
        """
        url  = f"{base_url}{self._CONNECT_PATH}"
        body = json.dumps({"application_name": APPLICATION_NAME}).encode()

        ssl_ctx = self._make_ssl_context()

        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                req,
                timeout=self._CONNECT_TIMEOUT,
                context=ssl_ctx,
            ) as resp:
                data = json.loads(resp.read())
                secret = data.get("secret", "")
                if not secret:
                    return ConnectResult(
                        error_message="Server approved but returned no secret.",
                    )
                return ConnectResult(success=True, secret=secret)

        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                return ConnectResult(
                    error_message=(
                        "Connection declined or timed out.\n"
                        "Please approve the connection in LightBurn / MillMage "
                        "when prompted."
                    ),
                )
            return ConnectResult(
                error_message=f"Server returned HTTP {exc.code}: {exc.reason}",
            )
        except urllib.error.URLError as exc:
            return ConnectResult(
                error_message=self._describe_url_error(exc),
            )
        except Exception as exc:
            return ConnectResult(error_message=f"Unexpected error: {exc}")

    # ------------------------------------------------------------------
    # File upload
    # ------------------------------------------------------------------

    def send(
        self,
        endpoint: Optional[EndpointConfig],
        file_bytes: bytes,
        fmt: str = "dxf",
    ) -> SendResult:
        """
        POST ``file_bytes`` to the endpoint's file-upload URL.

        Parameters
        ----------
        endpoint : EndpointConfig or None
            If None, returns an auth error prompting configuration.
        file_bytes : bytes
            Raw DXF or SVG content to POST.
        fmt : str
            ``'dxf'`` or ``'svg'`` — sets the ``X-Filename`` hint.

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

        url = f"{endpoint.url}{self._UPLOAD_PATH}"

        try:
            result = self._do_post(url, endpoint.token, file_bytes, fmt)
        except urllib.error.HTTPError as exc:
            return self._handle_http_error(exc)
        except urllib.error.URLError as exc:
            return SendResult(
                success=False,
                error_message=self._describe_url_error(exc),
            )
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
    def _make_ssl_context() -> ssl.SSLContext:
        """Self-signed certs are typical on a LAN."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        return ctx

    @staticmethod
    def _compute_bearer_token(secret: str) -> str:
        """
        Compute the HMAC-SHA256 time-based Bearer token.

        The server accepts tokens for the current minute and the
        previous minute to handle clock drift.
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
        ssl_ctx = self._make_ssl_context()
        bearer  = self._compute_bearer_token(secret)

        headers = {
            "Authorization":  f"Bearer {bearer}",
            "Content-Type":   self._CONTENT_TYPE,
            "X-Filename":     f"gear.{fmt}",
            "X-Group-Shapes": "true",
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
                    "The shared secret may be invalid or revoked."
                ),
            )
        return SendResult(
            success=False,
            http_status=status,
            error_message=f"Server returned HTTP {status}: {exc.reason}",
        )

    @staticmethod
    def _describe_url_error(exc: urllib.error.URLError) -> str:
        """Map connection/timeout errors to a user-friendly message."""
        reason = str(exc.reason)
        if "timed out" in reason.lower():
            return (
                "Connection timed out.  "
                "Make sure the REST listener is enabled in LightBurn / MillMage "
                "and that the host and port are correct."
            )
        if "refused" in reason.lower():
            return (
                "Connection refused.  "
                "The REST listener does not appear to be running.  "
                "Enable it in LightBurn / MillMage settings."
            )
        return (
            f"Could not connect: {reason}\n"
            "Check that the host IP and port are correct and that "
            "the REST listener is enabled."
        )
