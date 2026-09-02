"""Filesystem locations that differ between a source checkout and a frozen bundle.

PyInstaller unpacks read-only data into ``sys._MEIPASS``, which is a throwaway
temp dir in one-file mode and lives inside ``.app/Contents`` in one-dir mode.
Neither is a legal place to keep user state:

* one-file wipes ``_MEIPASS`` on exit, so anything written there is lost;
* writing inside a signed ``.app`` breaks the code signature seal, after which
  macOS refuses to launch the bundle.

So read-only resources resolve against the bundle, and everything the user can
change resolves against a per-user directory outside of it.
"""
from __future__ import annotations

import os
import sys

APP_NAME = "Text2SQL_Assistant"

# Project root when running from source (this file lives in <root>/app/).
_SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def resource_base() -> str:
    """Directory that bundled read-only data was unpacked into."""
    return getattr(sys, "_MEIPASS", _SOURCE_ROOT)


def resource_path(*parts: str) -> str:
    """Absolute path to a bundled read-only resource, e.g. ``resource_path("assets")``."""
    return os.path.join(resource_base(), *parts)


def user_data_dir() -> str:
    """Per-user, writable directory for config and other mutable state.

    Created on first call. Running from source keeps using the project root so
    the existing development workflow (and the checked-in ``config.json``) is
    unaffected.
    """
    if not is_frozen():
        return _SOURCE_ROOT

    if sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    elif os.name == "nt":
        base = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME)
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
        base = os.path.join(xdg, "text2sql-assistant")

    os.makedirs(base, exist_ok=True)
    return base


def user_config_path() -> str:
    """Absolute path to ``config.json`` in the writable user directory."""
    return os.path.join(user_data_dir(), "config.json")


def legacy_config_paths() -> list[str]:
    """Older config locations to migrate from, in priority order.

    Builds before the ``.app`` switch resolved the config relative to
    ``__file__``, which landed in ``_MEIPASS``. Some users may also have dropped
    a ``config.json`` next to the executable expecting it to be picked up.
    """
    candidates = [
        os.path.join(resource_base(), "config.json"),
        os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "config.json"),
    ]
    seen, out = set(), []
    for path in candidates:
        real = os.path.realpath(path)
        if real not in seen:
            seen.add(real)
            out.append(path)
    return out
