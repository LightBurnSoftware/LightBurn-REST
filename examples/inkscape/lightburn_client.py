"""
Self-contained REST client for the LightBurn / MillMage API.

Standalone copy (the Inkscape extension does not share SpurLine's client). Uses
only the standard library so it runs inside Inkscape's bundled Python.

Scope: pairing + file upload (the `upload` capability). Nothing else.
"""

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request

APPLICATION_NAME = "Inkscape"
CAPABILITIES = ["project", "upload"]   # project: read workspace; upload: send files

_CONNECT_TIMEOUT = 35   # 30 s consent dialog + buffer
_UPLOAD_TIMEOUT = 10


class LBError(Exception):
    """Anything the user needs to read and act on."""


# --- secret persistence -----------------------------------------------------

def _config_path():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "lightburn-rest", "inkscape-secrets.json")


def _load():
    try:
        with open(_config_path(), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save(secrets):
    path = _config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(secrets, fh)


# --- pairing + upload -------------------------------------------------------

def ensure_secret(base_url, application_name=APPLICATION_NAME):
    """Return a stored secret for base_url, pairing via /api/connect if none."""
    secrets = _load()
    if secrets.get(base_url):
        return secrets[base_url]
    secret = _connect(base_url, application_name)
    secrets[base_url] = secret
    _save(secrets)
    return secret


def _connect(base_url, application_name):
    body = json.dumps({
        "application_name": application_name,
        "capabilities": CAPABILITIES,
    }).encode()
    req = urllib.request.Request(
        base_url + "/api/connect", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_CONNECT_TIMEOUT) as resp:
            secret = json.loads(resp.read()).get("secret", "")
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            raise LBError("Pairing was declined or timed out. Approve the "
                          "request in LightBurn / MillMage, then run again.")
        raise LBError(f"Pairing failed: HTTP {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        raise LBError(f"Cannot reach the app at {base_url}. Is LightBurn / "
                      f"MillMage open? ({exc.reason})")
    if not secret:
        raise LBError("Server approved but returned no secret.")
    return secret


def _token(secret):
    message = str(int(time.time()) // 60).encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def _drop_secret(base_url):
    """Forget a stale secret so the next run re-pairs cleanly."""
    secrets = _load()
    secrets.pop(base_url, None)
    _save(secrets)


def get_project(base_url, secret):
    """GET /api/project — returns the parsed project metadata (workspace, units)."""
    req = urllib.request.Request(
        base_url + "/api/project", method="GET",
        headers={"Authorization": f"Bearer {_token(secret)}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_UPLOAD_TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            _drop_secret(base_url)
            raise LBError("Authorization failed (stored secret may be stale, or "
                          "lacks the 'project' scope). Run again to re-pair.")
        raise LBError(f"Could not read project: HTTP {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        raise LBError(f"Cannot reach the app at {base_url}. Is LightBurn / "
                      f"MillMage open? ({exc.reason})")


def upload(base_url, secret, data, filename, position=None, origin=None):
    """POST raw bytes to /api/file/upload. Returns the parsed 202 body.

    position : optional (x_mm, y_mm) workspace anchor for the import's bbox.
    origin   : optional bbox corner placed at position (e.g. "bottom-left").
    """
    headers = {
        "Authorization": f"Bearer {_token(secret)}",
        "Content-Type": "application/octet-stream",
        "X-Filename": filename,
    }
    if position is not None:
        headers["X-Position-X"] = f"{position[0]:g}"
        headers["X-Position-Y"] = f"{position[1]:g}"
        if origin:
            headers["X-Origin"] = origin
    req = urllib.request.Request(
        base_url + "/api/file/upload", data=data, method="POST", headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=_UPLOAD_TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            _drop_secret(base_url)
            raise LBError("Authorization failed (stored secret may be stale). "
                          "Run again to re-pair.")
        raise LBError(f"Upload failed: HTTP {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        raise LBError(f"Cannot reach the app at {base_url}. ({exc.reason})")
