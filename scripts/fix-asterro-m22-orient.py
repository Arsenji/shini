#!/usr/bin/env python3
"""Re-compose Asterro M22 truck wheel higher in the 900x1200 frame (no flip)."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/wheels"
DIST = ROOT / "dist/wheels"
BACKEND = ROOT / "backend/static/wheels"
TMP = ROOT / ".tmp-disk"
STEM = "asterro-m22-gruzovoy-nocolor"
SOURCE = PUBLIC / f"{STEM}.jpg"
TW, TH, FILL = 900, 1200, 0.83
# Top margin 3–5% of canvas height — wheel sits high, more white below.
TOP_MARGIN_FRAC = 0.04


def content_mask(arr: np.ndarray) -> np.ndarray:
    gray = arr.mean(axis=2)
    content = (gray < 245).astype(np.uint8) * 255
    content = cv2.morphologyEx(content, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), 2)
    n, lab, st, _ = cv2.connectedComponentsWithStats(content, 8)
    if n < 2:
        return content > 0
    main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return lab == main


def content_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def clean_on_white(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    gray = arr.mean(axis=2)
    pad = cv2.dilate(mask.astype(np.uint8) * 255, np.ones((5, 5), np.uint8), 2) > 0
    out = arr.copy()
    out[~pad] = (255, 255, 255)
    soft = (gray > 200) & (gray < 250) & ~pad
    out[soft] = (255, 255, 255)
    return out


def centroid_y_ratio(arr: np.ndarray) -> float:
    mask = content_mask(arr)
    ys, _ = np.where(mask)
    return float(ys.mean() / arr.shape[0])


def fit_canvas(arr: np.ndarray) -> Image.Image:
    mask = content_mask(arr)
    x0, y0, x1, y1 = content_bbox(mask)
    crop_arr = clean_on_white(arr, mask)
    crop = Image.fromarray(crop_arr).crop((max(0, x0 - 8), max(0, y0 - 8), x1 + 9, y1 + 9))
    tw, th = crop.size
    scale = min((TW * FILL) / tw, (TH * FILL) / th)
    nw, nh = max(1, int(tw * scale)), max(1, int(th * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    crop = ImageEnhance.Sharpness(crop).enhance(1.05)

    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    x = (TW - nw) // 2
    y = int(TH * TOP_MARGIN_FRAC)
    y = max(int(TH * 0.03), min(int(TH * 0.05), y))
    y = min(y, TH - nh - 48)

    sh_layer = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    blob = Image.fromarray((content_mask(np.array(crop)).astype(np.uint8) * 200))
    shadow = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 42), (0, 0), blob)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    sh_layer.paste(shadow, (x + 5, y + 12), shadow)
    base = canvas.convert("RGBA")
    base = Image.alpha_composite(base, sh_layer)
    base.paste(crop.convert("RGBA"), (x, y), crop.convert("RGBA"))
    return base.convert("RGB")


def save_outputs(canvas: Image.Image) -> None:
    for d in (PUBLIC, DIST, BACKEND):
        d.mkdir(parents=True, exist_ok=True)
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    canvas.save(full, "JPEG", quality=90, optimize=True)
    thimg = canvas.copy()
    thimg.thumbnail((360, 480))
    thimg.save(thumb, "JPEG", quality=85, optimize=True)
    for d in (DIST, BACKEND):
        (d / f"{STEM}.jpg").write_bytes(full.read_bytes())
        (d / f"{STEM}-thumb.jpg").write_bytes(thumb.read_bytes())
    TMP.mkdir(parents=True, exist_ok=True)
    canvas.save(TMP / "asterro-m22-lifted.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing source: {SOURCE}")
    raw = np.array(Image.open(SOURCE).convert("RGB"))
    before_top = content_bbox(content_mask(raw))[1]
    print(f"source={SOURCE.name}  top_before={before_top} ({before_top/TH*100:.1f}%)")

    canvas = fit_canvas(raw)
    arr = np.array(canvas)
    mask = content_mask(arr)
    top = content_bbox(mask)[1]
    bot = content_bbox(mask)[3]
    print(
        f"top_after={top} ({top/TH*100:.1f}%)  "
        f"bot={bot} ({bot/TH*100:.1f}%)  "
        f"centroid_y={centroid_y_ratio(arr):.3f}  fill={FILL}"
    )
    save_outputs(canvas)
    print("saved public/dist/backend + .tmp-disk/asterro-m22-lifted.jpg")


if __name__ == "__main__":
    main()
