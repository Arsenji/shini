#!/usr/bin/env python3
"""Force-remove thin embedded-photo frame lines from VENTI 1704 wheel JPG."""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/wheels"
DIST = ROOT / "dist/wheels"
BACKEND = ROOT / "backend/static/wheels"
TMP = ROOT / ".tmp-disk"
STEM = "venti-1704-66-1-litoy-chernyy-almaz"
SOURCE = PUBLIC / f"{STEM}.jpg"


def _runs(indices: np.ndarray, gap: int = 2) -> list[tuple[int, int]]:
    if len(indices) == 0:
        return []
    breaks = np.where(np.diff(indices) > gap)[0]
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [len(indices) - 1]))
    return [(int(indices[s]), int(indices[e])) for s, e in zip(starts, ends)]


def wheel_bbox(img: np.ndarray) -> tuple[int, int, int, int]:
    mean = img.mean(axis=2)
    ys, xs = np.where(mean < 250)
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def count_near_black_outside(
    img: np.ndarray, x0: int, x1: int, y0: int, y1: int, *, left_cols: int = 0, bottom_rows: int = 0
) -> dict[str, int]:
    h, w = img.shape[:2]
    nb = img.max(axis=2) < 40
    out: dict[str, int] = {}
    if left_cols:
        sub = nb[:, :left_cols]
        mask = np.ones(sub.shape, dtype=bool)
        for y in range(h):
            for x in range(left_cols):
                if y0 <= y <= y1 and x0 <= x <= x1:
                    mask[y, x] = False
        out[f"left{left_cols}"] = int((sub & mask).sum())
    if bottom_rows:
        sub = nb[-bottom_rows:, :]
        mask = np.ones(sub.shape, dtype=bool)
        base = h - bottom_rows
        for y in range(bottom_rows):
            gy = base + y
            for x in range(w):
                if y0 <= gy <= y1 and x0 <= x <= x1:
                    mask[y, x] = False
        out[f"bottom{bottom_rows}"] = int((sub & mask).sum())
    return out


def print_near_black_report(img: np.ndarray, x0: int, x1: int, y0: int, y1: int) -> None:
    h, w = img.shape[:2]
    nb = img.max(axis=2) < 40

    print("=== Near-black pixels (max channel < 40) ===")
    left = nb[:, :100]
    mask = np.ones(left.shape, dtype=bool)
    for y in range(h):
        for x in range(100):
            if y0 <= y <= y1 and x0 <= x <= x1:
                mask[y, x] = False
    outside = left & mask
    if outside.any():
        ys = np.where(outside.any(axis=1))[0]
        print(f"left 100 cols outside wheel: count={int(outside.sum())}, y-ranges={_runs(ys)}")
    else:
        print("left 100 cols outside wheel: none")

    bottom = nb[-100:, :]
    bmask = np.ones(bottom.shape, dtype=bool)
    base = h - 100
    for y in range(100):
        gy = base + y
        for x in range(w):
            if y0 <= gy <= y1 and x0 <= x <= x1:
                bmask[y, x] = False
    bout = bottom & bmask
    if bout.any():
        ys = np.where(bout.any(axis=1))[0] + base
        print(f"bottom 100 rows outside wheel: count={int(bout.sum())}, y-ranges={_runs(ys)}")
    else:
        print("bottom 100 rows outside wheel: none")


def local_mean(img: np.ndarray, ksize: int = 11) -> np.ndarray:
    gray = img.mean(axis=2).astype(np.float32)
    return cv2.GaussianBlur(gray, (ksize, ksize), 0)


def vertical_line_on_white(img: np.ndarray, x: int, y: int, neigh: np.ndarray) -> bool:
    if img[y, x].max() >= 50:
        return False
    if neigh[y, x] <= 240:
        return False
    h = img.shape[0]
    same_col = [yy for yy in (y - 1, y + 1) if 0 <= yy < h and img[yy, x].max() < 80]
    if len(same_col) < 1:
        return False
    return True


def horizontal_line_on_white(img: np.ndarray, x: int, y: int, neigh: np.ndarray) -> bool:
    if img[y, x].max() >= 50:
        return False
    if neigh[y, x] <= 240:
        return False
    w = img.shape[1]
    same_row = [xx for xx in (x - 1, x + 1) if 0 <= xx < w and img[y, xx].max() < 80]
    if len(same_row) < 1:
        return False
    return True


def margin_strip_masks(img: np.ndarray, neigh: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Thin vertical/horizontal strips within 80px of canvas edges on white background."""
    h, w = img.shape[:2]
    maxc = img.max(axis=2)
    dark = maxc < 180

    vert = np.zeros((h, w), dtype=bool)
    for x in range(min(80, w)):
        ys = np.where(dark[:, x] & (neigh[:, x] > 228))[0]
        for a, b in _runs(ys):
            if b - a + 1 >= 20:
                vert[a : b + 1, x] = True

    horiz = np.zeros((h, w), dtype=bool)
    for y in range(max(0, h - 80), h):
        xs = np.where(dark[y, :] & (neigh[y, :] > 228))[0]
        for a, b in _runs(xs):
            if b - a + 1 >= 20:
                horiz[y, a : b + 1] = True

    return vert, horiz


def build_clean_mask(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    neigh = local_mean(img)
    maxc = img.max(axis=2)
    mask = np.zeros((h, w), dtype=bool)

    # 4) Nuclear: all channels < 50 on mostly-white neighborhood.
    mask |= (img[:, :, 0] < 50) & (img[:, :, 1] < 50) & (img[:, :, 2] < 50) & (neigh > 240)

    # Gray frame lines on white (safe globally for this image; blur ~229 on line pixels).
    gray_frame = (maxc < 180) & (neigh > 228)
    mask |= gray_frame

    # 3) Left 0-120: near-black vertical line pixels on white.
    for x in range(min(120, w)):
        for y in range(h):
            if vertical_line_on_white(img, x, y, neigh):
                mask[y, x] = True

    # 3) Bottom 50 rows: near-black horizontal line pixels on white.
    for y in range(max(0, h - 50), h):
        for x in range(w):
            if horizontal_line_on_white(img, x, y, neigh):
                mask[y, x] = True

    # 3) Right edge similarly.
    for x in range(max(0, w - 80), w):
        for y in range(h):
            if vertical_line_on_white(img, x, y, neigh):
                mask[y, x] = True

    # 5) Margin strips within 80px of canvas edge.
    vert, horiz = margin_strip_masks(img, neigh)
    mask |= vert | horiz

    return mask


def clean_image(img: np.ndarray) -> tuple[np.ndarray, int]:
    out = img.copy()
    total = 0
    for _ in range(4):
        mask = build_clean_mask(out)
        if not mask.any():
            break
        out[mask] = (255, 255, 255)
        total += int(mask.sum())
    return out, total


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
    canvas.save(TMP / "venti1704-clean-edges.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    raw = np.array(Image.open(SOURCE).convert("RGB"))
    h, w = raw.shape[:2]
    x0, x1, y0, y1 = wheel_bbox(raw)
    print(f"source={SOURCE.name} size={w}x{h} wheel_bbox=x{x0}-{x1} y{y0}-{y1}")

    before = count_near_black_outside(raw, x0, x1, y0, y1, left_cols=80, bottom_rows=80)
    print_near_black_report(raw, x0, x1, y0, y1)
    print(f"BEFORE near-black outside wheel: {before}")

    cleaned, removed = clean_image(raw)
    after = count_near_black_outside(cleaned, x0, x1, y0, y1, left_cols=80, bottom_rows=80)
    print(f"pixels_whitened={removed}")
    print(f"AFTER near-black outside wheel: {after}")

    if any(v != 0 for v in after.values()):
        raise SystemExit(f"QA failed: near-black remains outside wheel: {after}")

    neigh = local_mean(cleaned)
    gray_left = int(((cleaned.max(axis=2) < 180) & (neigh > 228))[:, :120].sum())
    gray_bottom = int(((cleaned.max(axis=2) < 180) & (neigh > 228))[-80:, :].sum())
    print(f"AFTER gray frame remnants left120={gray_left} bottom80={gray_bottom}")
    if gray_left or gray_bottom:
        raise SystemExit("QA failed: gray frame line pixels remain")

    save_outputs(Image.fromarray(cleaned))
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size} bytes {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size} bytes {Image.open(thumb).size}")
    print("saved public/dist/backend + .tmp-disk/venti1704-clean-edges.jpg")


if __name__ == "__main__":
    main()
