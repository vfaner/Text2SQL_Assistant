#!/usr/bin/env python3
"""
Regenerate the platform icon files from the master artwork.

    python scripts/make_icons.py

Reads `assets/app_icon.png` (a square RGBA image, ideally 1024x1024 with
transparent corners) and writes:

* `assets/app_icon.icns` — macOS bundle icon, via `iconutil`
* `assets/app_icon.ico`  — Windows executable icon

Requires macOS, since it shells out to `sips` and `iconutil`. The `.ico` writer
embeds PNG payloads, which Windows has understood since Vista; that keeps this
script free of any image-library dependency.
"""
from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "assets" / "app_icon.png"
ICNS = ROOT / "assets" / "app_icon.icns"
ICO = ROOT / "assets" / "app_icon.ico"

# (pixel size, filename) pairs iconutil expects in an .iconset directory.
ICONSET_LAYERS = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def resize(src: Path, size: int, dest: Path) -> bytes:
    """Scale `src` to size x size with sips and return the PNG bytes."""
    subprocess.run(
        ["sips", "-s", "format", "png", "-z", str(size), str(size),
         str(src), "--out", str(dest)],
        check=True, capture_output=True,
    )
    data = dest.read_bytes()
    if not data.startswith(PNG_MAGIC):
        raise RuntimeError(f"sips did not produce a PNG at {size}px")
    return data


def build_icns(work: Path) -> None:
    iconset = work / "app_icon.iconset"
    iconset.mkdir()
    for size, name in ICONSET_LAYERS:
        resize(MASTER, size, iconset / name)
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(ICNS)],
                   check=True)
    print(f"  {ICNS.relative_to(ROOT)}  {ICNS.stat().st_size:,} bytes"
          f"  {len(ICONSET_LAYERS)} layers")


def build_ico(work: Path) -> None:
    images = [(s, resize(MASTER, s, work / f"ico_{s}.png")) for s in ICO_SIZES]

    offset = 6 + 16 * len(images)
    entries, blobs = [], []
    for size, data in images:
        # A 256px entry is recorded as 0 — the field is a single byte.
        dim = 0 if size >= 256 else size
        entries.append(
            struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        )
        blobs.append(data)
        offset += len(data)

    header = struct.pack("<HHH", 0, 1, len(images))
    ICO.write_bytes(header + b"".join(entries) + b"".join(blobs))
    print(f"  {ICO.relative_to(ROOT)}  {ICO.stat().st_size:,} bytes"
          f"  {len(images)} resolutions")


def main() -> int:
    if sys.platform != "darwin":
        print("error: needs macOS (uses sips and iconutil)", file=sys.stderr)
        return 1
    if not MASTER.exists():
        print(f"error: missing master artwork {MASTER}", file=sys.stderr)
        return 1
    for tool in ("sips", "iconutil"):
        if shutil.which(tool) is None:
            print(f"error: {tool} not found on PATH", file=sys.stderr)
            return 1

    work = Path(tempfile.mkdtemp(prefix="text2sql-icons-"))
    try:
        print(f"master: {MASTER.relative_to(ROOT)}")
        build_icns(work)
        build_ico(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
