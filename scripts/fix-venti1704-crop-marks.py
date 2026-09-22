#!/usr/bin/env python3
"""Remove thin black crop-mark borders from VENTI 1704 wheel JPG (no flip/reorient)."""

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


def detect_crop_marks(gray: np.ndarray) -> np.ndarray:
    """Near-black embedded-photo frame lines on white background."""
    h, w = gray.shape
    marks = np.zeros((h, w), bool)
    white = gray > 240

    # Left vertical frame strip (x=72-79).
    for x in range(72, min(w, 80)):
        marks[:, x] = gray[:, x] < 80

    # Bottom outer frame strip (y=971-977) across embedded photo width.
    for y in range(971, min(h, 978)):
        marks[y, 72:min(w, 828)] = gray[y, 72:min(w, 828)] < 80

    # Inner bottom horizontal crop mark above the soft ground shadow.
    for y in range(934, 957):
        if white[y].sum() / w < 0.55:
            continue
        white_x = np.where(white[y])[0]
        if len(white_x) == 0:
            continue
        xs = np.where((gray[y] < 50) & (np.arange(w) >= 85) & (np.arange(w) <= 830))[0]
        for x in xs:
            # Line pixel on a mostly-white row with white background nearby on the same row.
            left_white = np.any(white_x < x) and (x - white_x[white_x < x][-1]) <= 400
            right_white = np.any(white_x > x) and (white_x[white_x > x][0] - x) <= 400
            if left_white or right_white:
                marks[y, x] = True

    # Slight dilation for anti-aliased border pixels.
    dilated = cv2.dilate(marks.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 1) > 0
    return dilated & (gray < 90)


def clean_image(img: np.ndarray) -> tuple[np.ndarray, int]:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    marks = detect_crop_marks(gray)
    count = int(marks.sum())
    if count == 0:
        return img, 0

    out = img.copy()
    h, w = gray.shape
    # Outer frame strips always become pure white (not inpaint).
    outer = np.zeros((h, w), bool)
    outer[:, 72:min(w, 80)] = True
    outer[971:min(h, 978), 72:min(w, 828)] = True
    white_replace = marks & outer
    inpaint = marks & ~outer

    out[white_replace] = (255, 255, 255)
    if inpaint.any():
        mask = cv2.dilate(inpaint.astype(np.uint8) * 255, np.ones((2, 2), np.uint8), 1)
        out = cv2.inpaint(out, mask, 3, cv2.INPAINT_TELEA)

    return out, count


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
    canvas.save(TMP / "venti1704-nolines.jpg", "JPEG", quality=90, optimize=True)


def qa_no_border_lines(gray: np.ndarray) -> dict[str, int | bool]:
    """Confirm crop-mark zones no longer contain long near-black runs."""
    h, w = gray.shape
    white = gray > 240
    issues = 0

    # Left strip
    for x in range(72, min(w, 80)):
        ys = np.where(gray[:, x] < 50)[0]
        for a, b in _runs(ys):
            if b - a + 1 >= 20:
                issues += 1

    # Bottom outer strip
    for y in range(971, min(h, 978)):
        xs = np.where(gray[y, 72:min(w, 828)] < 50)[0]
        for a, b in _runs(xs):
            if b - a + 1 >= 20:
                issues += 1

    # Inner bottom band on white rows (long runs only; short wheel-edge stubs ignored)
    for y in range(940, 957):
        if white[y].sum() / w < 0.55:
            continue
        xs = np.where((gray[y] < 50) & (np.arange(w) >= 85) & (np.arange(w) <= 830))[0]
        for a, b in _runs(xs):
            if b - a + 1 >= 30:
                issues += 1

    return {"border_line_runs": issues, "clean": issues == 0}


def main() -> None:
    raw = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={raw.shape[1]}x{raw.shape[0]}")

    cleaned, px = clean_image(raw)
    print(f"crop_mark_pixels_removed={px}")

    qa = qa_no_border_lines(cv2.cvtColor(cleaned, cv2.COLOR_RGB2GRAY))
    print(f"QA: {qa}")
    if not qa["clean"]:
        raise SystemExit(f"QA failed: still see border line runs ({qa['border_line_runs']})")

    save_outputs(Image.fromarray(cleaned))
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size} bytes {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size} bytes {Image.open(thumb).size}")
    print("saved public/dist/backend + .tmp-disk/venti1704-nolines.jpg")


if __name__ == "__main__":
    main()
