#!/usr/bin/env python3
"""Process user-provided VENTI 1704 photo (already face-right)."""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/wheels"
DIST = ROOT / "dist/wheels"
BACKEND = ROOT / "backend/static/wheels"
TMP = ROOT / ".tmp-disk"
STEM = "venti-1704-66-1-litoy-chernyy-almaz"
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/image-f4f5504d-4333-416e-9fa4-cd0ebce41770.png"
)
TW, TH, FILL = 900, 1200, 0.84


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


def barrel_on_left(mask: np.ndarray) -> bool:
    ys, xs = np.where(mask)
    cx = xs.mean()
    return (xs < cx).sum() > (xs >= cx).sum()


def _hub_mask(wheel: np.ndarray) -> np.ndarray:
    ys, xs = np.where(wheel)
    cy, cx = int(ys.mean()), int(xs.mean())
    y0, y1 = ys.min(), ys.max()
    r = int((y1 - y0) * 0.17)
    yy, xx = np.ogrid[: wheel.shape[0], : wheel.shape[1]]
    return ((yy - cy) ** 2 + (xx - cx) ** 2) <= r * r


def gentle_diagonal_watermark_mask(img: np.ndarray, wheel: np.ndarray) -> np.ndarray:
    """Detect faint low-contrast gray diagonal watermark on dark wheel surfaces."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    local = cv2.GaussianBlur(gray, (0, 0), 7)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)

    # Light gray overlay on dark/black spokes
    lifted = (gray - local) > 8
    grayish = (gray > 95) & (gray < 215) & (sat < 55)
    dark_base = local < 140

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    diag = mag > 18

    hub = _hub_mask(wheel)
    wm = wheel & ~hub & lifted & grayish & dark_base & diag
    wm = cv2.morphologyEx(wm.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), 1) > 0
    return wm


def remove_watermark(img: np.ndarray) -> tuple[np.ndarray, int]:
    wheel = content_mask(img)
    wm = gentle_diagonal_watermark_mask(img, wheel)
    count = int(wm.sum())
    if count < 40:
        return img, count
    out = img.copy()
    mask = cv2.dilate(wm.astype(np.uint8) * 255, np.ones((2, 2), np.uint8), 1)
    out = cv2.inpaint(out, mask, 3, cv2.INPAINT_TELEA)
    return out, count


def scrub_background(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    out = img.copy()
    gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
    tight = gray < 228
    tight = cv2.morphologyEx(tight.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), 1) > 0
    pad = cv2.dilate(tight.astype(np.uint8) * 255, np.ones((6, 6), np.uint8), 1) > 0
    out[(~pad) & (gray < 252)] = (255, 255, 255)
    x0, _, x1, y1 = content_bbox(tight)
    below = np.arange(h)[:, None] > min(h - 1, y1 + 2)
    out[below & (gray < 250)] = (255, 255, 255)
    side = (np.arange(w)[None, :] < max(0, x0 - 6)) | (np.arange(w)[None, :] > min(w - 1, x1 + 6))
    out[below & side & (gray < 250)] = (255, 255, 255)
    return out


def add_soft_shadow(canvas: Image.Image) -> Image.Image:
    arr = np.array(canvas)
    mask = content_mask(arr)
    if not mask.any():
        return canvas
    x0, y0, x1, y1 = content_bbox(mask)
    shadow = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    oval = Image.new("L", canvas.size, 0)
    cx, cy = (x0 + x1) // 2, y1 + 18
    rx, ry = int((x1 - x0) * 0.38), 16
    from PIL import ImageDraw

    draw = ImageDraw.Draw(oval)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=90)
    oval = oval.filter(ImageFilter.GaussianBlur(12))
    shadow.paste((220, 220, 220), mask=oval)
    base = canvas.convert("RGBA")
    base.alpha_composite(shadow)
    return base.convert("RGB")


def fit_canvas(arr: np.ndarray) -> Image.Image:
    mask = content_mask(arr)
    x0, y0, x1, y1 = content_bbox(mask)
    pad = cv2.dilate(mask.astype(np.uint8) * 255, np.ones((5, 5), np.uint8), 2) > 0
    crop_arr = arr.copy()
    crop_arr[~pad] = (255, 255, 255)
    crop = Image.fromarray(crop_arr).crop((max(0, x0 - 8), max(0, y0 - 8), x1 + 9, y1 + 9))
    tw, th = crop.size
    scale = min((TW * FILL) / tw, (TH * FILL) / th)
    nw, nh = max(1, int(tw * scale)), max(1, int(th * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    crop = ImageEnhance.Sharpness(crop).enhance(1.05)
    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    x = (TW - nw) // 2
    y = (TH - nh) // 2
    canvas.paste(crop, (x, y))
    return add_soft_shadow(canvas)


def save_outputs(canvas: Image.Image) -> None:
    for d in (PUBLIC, DIST, BACKEND):
        d.mkdir(parents=True, exist_ok=True)
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    canvas.save(full, "JPEG", quality=90, optimize=True)
    thimg = canvas.copy()
    thimg.thumbnail((360, 480), Image.Resampling.LANCZOS)
    thimg.save(thumb, "JPEG", quality=85, optimize=True)
    for d in (DIST, BACKEND):
        shutil.copy2(full, d / f"{STEM}.jpg")
        shutil.copy2(thumb, d / f"{STEM}-thumb.jpg")
    TMP.mkdir(parents=True, exist_ok=True)
    canvas.save(TMP / "venti1704-new.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    raw = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={raw.shape[1]}x{raw.shape[0]} mode=RGB")
    mask = content_mask(raw)
    print(f"barrel_on_left={barrel_on_left(mask)} (False = face-right, no flip needed)")

    cleaned, wm_px = remove_watermark(raw)
    print(f"watermark_pixels_inpainted={wm_px}")

    canvas = fit_canvas(scrub_background(cleaned))
    save_outputs(canvas)

    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size} bytes {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size} bytes {Image.open(thumb).size}")
    print("saved public/dist/backend + .tmp-disk/venti1704-new.jpg")


if __name__ == "__main__":
    main()
