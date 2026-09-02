# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the Text2SQL Assistant desktop app.

Bundles the `assets/` directory (icons, QR codes, screenshots) and produces:

* macOS  — a one-dir build wrapped in `Text2SQL_Assistant.app`. A bundle is
           required because Gatekeeper offers no way to approve a bare Unix
           executable: the "unverified developer" dialog for one only has
           "Move to Trash". Build via `scripts/build_macos.sh`, which also
           ad-hoc signs the bundle and wraps it in a DMG.
* Windows / Linux — a single-file executable, as before.

App artwork lives in `assets/`: `app_icon.png` (1024x1024 master, also used for
the Qt window icon), `app_icon.icns` for the macOS bundle, `app_icon.ico` for
the Windows executable. Regenerate the latter two with
`scripts/make_icons.py` after changing the master.

Run with:

    pyinstaller --clean --noconfirm Text2SQL_Assistant.spec

Output lands under `dist/`.
"""

import re
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"

# Single source of truth for the version: app/__init__.py. Parsed rather than
# imported so Analysis isn't preceded by a PySide6 import in this process.
_init = Path("app/__init__.py").read_text(encoding="utf-8")
VERSION = re.search(r'__version__\s*=\s*"([^"]+)"', _init).group(1)

# Bundle the whole assets directory; app/paths.py resolves it via sys._MEIPASS.
datas = [("assets", "assets")]

# SQLAlchemy dialects import their driver modules lazily, so a few extra
# hidden imports keep the builds honest.
hiddenimports = (
    collect_submodules("sqlalchemy.dialects")
    + [
        "pymysql",
        "psycopg2",
        # cx_Oracle / pyodbc / dmPython are optional; add here if you bundle them
    ]
)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "pytest",
        "pydoc_data",
        # ~11 MB, and nothing imports it. It only gets pulled in because
        # requests/__init__.py touches it inside a `try/except ImportError`
        # to warn about old versions on the legacy pyopenssl path — static
        # analysis can't see that guard. Verified: requests still does HTTPS
        # fine without it. Drop this exclude if app/config.py is ever switched
        # from base64 obfuscation to real cryptography-backed encryption.
        "cryptography",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# ── macOS: one-dir + .app bundle ─────────────────────────────────────────
if IS_MACOS:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,      # binaries/datas go into COLLECT instead
        name="Text2SQL_Assistant",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,              # windowed / GUI app: no console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,           # auto per runner
        # Signing is done in scripts/build_macos.sh, after xattrs are cleared —
        # leftover extended attributes would otherwise be sealed into the
        # signature and fail `codesign --verify --strict`.
        codesign_identity=None,
        entitlements_file=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="Text2SQL_Assistant",
    )

    app = BUNDLE(
        coll,
        name="Text2SQL_Assistant.app",
        icon="assets/app_icon.icns",
        bundle_identifier="io.github.vfaner.text2sql-assistant",
        version=VERSION,
        info_plist={
            "CFBundleName": "Text2SQL Assistant",
            "CFBundleDisplayName": "Text2SQL Assistant",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "LSMinimumSystemVersion": "11.0",
            "LSApplicationCategoryType": "public.app-category.developer-tools",
            "NSHighResolutionCapable": True,
            # The Qt stylesheet in app/styles.py is a light theme (#f5f7fa),
            # so opt out of automatic dark-mode repainting.
            "NSRequiresAquaSystemAppearance": True,
            "NSHumanReadableCopyright": "MIT License",
        },
    )

# ── Windows / Linux: single-file executable ──────────────────────────────
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="Text2SQL_Assistant",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,              # windowed / GUI app: no console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        # Linux executables carry no icon resource, so only pass it on Windows.
        icon="assets/app_icon.ico" if IS_WINDOWS else None,
    )
