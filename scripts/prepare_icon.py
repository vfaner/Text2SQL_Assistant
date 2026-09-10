#!/usr/bin/env python3
"""
Cut the icon artwork out of its photo background.

    python3 scripts/prepare_icon.py assets/icon.jpg

The Doubao-generated artwork ships as a 1280x1280 JPEG: the rounded-square
glass plate sits on a light studio background with a soft drop shadow. This
script turns it into a flat app icon:

* crops tightly to the plate and writes a square 1024x1024 RGBA master
  `assets/app_icon.png` with transparent corners/background and no shadow;
* the plate's own white/silver bevel inside the cyan rim is preserved;
* a thin band of vivid cyan glow just outside the rim is kept so the neon
  edge survives the geometric cut.

Geometry (plate edges, corner radius) was measured from `assets/icon.jpg`;
if the source artwork changes, the constants below need remeasuring.

After this, run `python3 scripts/make_icons.py` to regenerate the `.icns`
and `.ico`. Requires PySide6 (already a project dependency).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QColor, QPainter, QPainterPath

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "assets" / "app_icon.png"

# Plate geometry in source-image pixels (measured for assets/icon.jpg,
# 1280x1280). CORE is inset ~5px from the photographic plate edge so that
# near-white background fringe never survives; the glow band restores the
# saturated rim beyond it.
CORE_RECT = (165, 197, 1149, 1087)   # L, T, R, B after the 5px inset
CORNER_RADIUS = 158
GLOW_BAND = 18                       # px outside CORE allowed for cyan glow


def rounded_rect(path: QPainterPath, l: int, t: int, r: int, b: int, rad: int) -> None:
    path.addRoundedRect(QRectF(l, t, r - l, b - t), rad, rad)


def main() -> int:
    src_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "assets" / "icon.jpg"
    if not src_path.exists():
        print(f"error: source artwork not found: {src_path}", file=sys.stderr)
        return 1

    src = QImage(str(src_path)).convertToFormat(QImage.Format_RGB32)

    l, t, r, b = CORE_RECT
    core = QPainterPath()
    rounded_rect(core, l, t, r, b, CORNER_RADIUS)

    outer = QPainterPath()
    rounded_rect(outer, l - GLOW_BAND, t - GLOW_BAND, r + GLOW_BAND, b + GLOW_BAND,
                 CORNER_RADIUS + GLOW_BAND)
    band = outer.subtracted(core)

    canvas = QImage(src.width(), src.height(), QImage.Format_ARGB32)
    canvas.fill(0)
    p = QPainter(canvas)
    p.setRenderHint(QPainter.Antialiasing)

    # Opaque plate body.
    p.setClipPath(core)
    p.drawImage(0, 0, src)

    # Cyan neon rim just outside the cut. Isolated bluish shadow speckles
    # fail the saturation threshold and stay transparent.
    glow = QImage(src.width(), src.height(), QImage.Format_ARGB32)
    glow.fill(0)
    gp = QPainter(glow)
    for y in range(t - GLOW_BAND - 4, b + GLOW_BAND + 4):
        for x in range(l - GLOW_BAND - 4, r + GLOW_BAND + 4):
            c = src.pixelColor(x, y)
            rr, gg, bb = c.red(), c.green(), c.blue()
            if bb - rr > 55 and gg - rr > 15 and bb > 100:
                a = min(255, int((bb - rr - 55) * 5))
                gp.setPen(QColor(rr, gg, bb, a))
                gp.drawPoint(x, y)
    gp.end()

    p.setClipPath(band)
    p.drawImage(0, 0, glow)
    p.end()

    # Square crop centered on the plate, then downscale to 1024.
    x0, y0 = l - GLOW_BAND, t - GLOW_BAND
    x1, y1 = r + GLOW_BAND, b + GLOW_BAND
    side = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    ox, oy = cx - side // 2, cy - side // 2
    master = canvas.copy(ox, oy, side, side).scaled(
        1024, 1024, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    if not master.save(str(MASTER)):
        print(f"error: failed to write {MASTER}", file=sys.stderr)
        return 1
    print(f"  {MASTER.relative_to(ROOT)}  1024x1024 RGBA (cropped from {src_path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
