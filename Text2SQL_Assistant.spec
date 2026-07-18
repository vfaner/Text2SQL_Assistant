# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the Text2SQL Assistant desktop app.

Produces a single-file, windowed executable that includes the
`assets/` directory (icons, QR codes, screenshots). Run with:

    pyinstaller --clean --noconfirm Text2SQL_Assistant.spec

The generated binary lives under `dist/`.
"""

from PyInstaller.utils.hooks import collect_submodules

# Bundle the whole assets directory next to the executable / inside _MEIPASS.
datas = [("assets", "assets")]

# SQLAlchemy dialects import their driver modules lazily, so a few extra
# hidden imports keep single-file builds honest.
hiddenimports = (
    collect_submodules("sqlalchemy.dialects")
    + [
        "pymysql",
        "psycopg2",
        # cx_Oracle / pyodbc / dmPython are optional; add here if you bundle them
    ]
)

block_cipher = None

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
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Text2SQL_Assistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # windowed / GUI app: no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,        # auto per runner
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/app_icon.ico" — set if you later add a Windows/macOS app icon
)
