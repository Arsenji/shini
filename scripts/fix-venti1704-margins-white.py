#!/usr/bin/env python3
"""Nuclear margin wipe: white everything outside padded wheel bbox + edge line cleanup."""

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

PADDING = 15
EDGE_BAND = 5


def _runs(indices: np.ndarray, gap: int = 2) -> list[tuple[int, int]]:
    if len(indices) == 0:
        return []
    breaks = np.where(np.diff(indices) > gap)[0]
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [len(indices) - 1]))
    return [(int(indices[s]), int(indices[e])) for s, e in zip(starts, ends)]


def wheel_content_mask(img: np.ndarray) -> np.ndarray:
    """Non-white wheel pixels (gray mean < 245), largest connected component."""
    gray = img.mean(axis=2)
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


def expand_bbox(
    x0: int, y0: int, x1: int, y1: int, pad: int, w: int, h: int
) -> tuple[int, int, int, int]:
    return (
        max(0, x0 - pad),
        max(0, y0 - pad),
        min(w - 1, x1 + pad),
        min(h - 1, y1 + pad),
    )


def local_mean(img: np.ndarray, ksize: int = 11) -> np.ndarray:
    gray = img.mean(axis=2).astype(np.float32)
    return cv2.GaussianBlur(gray, (ksize, ksize), 0)


def margin_ring_line_mask(
    img: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    px0: int,
    py0: int,
    px1: int,
    py1: int,
) -> np.ndarray:
    """Detect thin gray/black line segments on white in the full padding ring."""
    h, w = img.shape[:2]
    neigh = local_mean(img)
    maxc = img.max(axis=2)

    ring = np.zeros((h, w), dtype=bool)
    ring[py0 : py1 + 1, px0 : px1 + 1] = True
    ring[y0 : y1 + 1, x0 : x1 + 1] = False

    dark = maxc < 180
    on_white = neigh > 228
    mask = np.zeros((h, w), dtype=bool)

    ys, xs = np.where(ring)
    for y, x in zip(ys, xs):
        if not (dark[y, x] and on_white[y, x]):
            continue
        # Vertical run check
        vrun = 1
        for yy in range(y - 1, -1, -1):
            if ring[yy, x] and dark[yy, x]:
                vrun += 1
            else:
                break
        for yy in range(y + 1, h):
            if ring[yy, x] and dark[yy, x]:
                vrun += 1
            else:
                break
        # Horizontal run check
        hrun = 1
        for xx in range(x - 1, -1, -1):
            if ring[y, xx] and dark[y, xx]:
                hrun += 1
            else:
                break
        for xx in range(x + 1, w):
            if ring[y, xx] and dark[y, xx]:
                hrun += 1
            else:
                break
        if vrun >= 8 or hrun >= 8 or maxc[y, x] < 50:
            mask[y, x] = True

    # Also wipe any gray/dark pixel in ring sitting on bright background.
    mask |= ring & dark & on_white
    return mask


def edge_line_mask(img: np.ndarray, x0: int, y0: int, x1: int, y1: int, px0: int, py0: int, px1: int, py1: int) -> np.ndarray:
    """Thin gray/black line segments within 5px of wheel bbox edges (inside padding ring)."""
    h, w = img.shape[:2]
    neigh = local_mean(img)
    maxc = img.max(axis=2)
    dark = maxc < 180
    on_white = neigh > 228

    band = np.zeros((h, w), dtype=bool)
    for x in range(max(px0, x0 - EDGE_BAND), min(w, x0 + 1)):
        band[:, x] = True
    for x in range(max(px0, x1 - EDGE_BAND + 1), min(w, px1 + 1)):
        band[:, x] = True
    for y in range(max(py0, y0 - EDGE_BAND), min(h, y0 + 1)):
        band[y, :] = True
    for y in range(max(py0, y1 - EDGE_BAND + 1), min(h, py1 + 1)):
        band[y, :] = True

    mask = np.zeros((h, w), dtype=bool)
    for x in range(w):
        if not band[:, x].any():
            continue
        ys = np.where(dark[:, x] & on_white[:, x] & band[:, x])[0]
        for a, b in _runs(ys):
            if b - a + 1 >= 8:
                mask[a : b + 1, x] = True

    for y in range(h):
        if not band[y, :].any():
            continue
        xs = np.where(dark[y, :] & on_white[y, :] & band[y, :])[0]
        for a, b in _runs(xs):
            if b - a + 1 >= 8:
                mask[y, a : b + 1] = True

    mask |= band & dark & on_white & (maxc < 50)
    return mask


def nuclear_margin_wipe(img: np.ndarray) -> tuple[np.ndarray, dict]:
    h, w = img.shape[:2]
    mask = wheel_content_mask(img)
    x0, y0, x1, y1 = content_bbox(mask)
    px0, py0, px1, py1 = expand_bbox(x0, y0, x1, y1, PADDING, w, h)

    out = img.copy()
    outside = np.ones((h, w), dtype=bool)
    outside[py0 : py1 + 1, px0 : px1 + 1] = False
    outside_px = int(outside.sum())
    out[outside] = (255, 255, 255)

    line_mask = edge_line_mask(out, x0, y0, x1, y1, px0, py0, px1, py1)
    line_mask |= margin_ring_line_mask(out, x0, y0, x1, y1, px0, py0, px1, py1)
    line_px = int(line_mask.sum())
    out[line_mask] = (255, 255, 255)

    # Final pass: any non-pure-white pixel in padding ring on white → white.
    ring = np.zeros((h, w), dtype=bool)
    ring[py0 : py1 + 1, px0 : px1 + 1] = True
    ring[y0 : y1 + 1, x0 : x1 + 1] = False
    ring_gray = ring & (out.max(axis=2) < 250) & (local_mean(out) > 235)
    ring_px = int(ring_gray.sum())
    out[ring_gray] = (255, 255, 255)

    meta = {
        "wheel_bbox": (x0, y0, x1, y1),
        "padded_bbox": (px0, py0, px1, py1),
        "outside_whitened": outside_px,
        "edge_lines_whitened": line_px,
        "ring_gray_whitened": ring_px,
    }
    return out, meta


def qa_margins(img: np.ndarray, px0: int, py0: int, px1: int, py1: int) -> dict:
    """Confirm left/right/bottom margin zones are pure white with no dark line runs."""
    h, w = img.shape[:2]
    gray = img.mean(axis=2)
    issues: list[str] = []

    def check_zone(name: str, zone: np.ndarray, axis: int, min_run: int = 12) -> None:
        dark = zone < 245
        if not dark.any():
            return
        if axis == 0:  # vertical runs along y
            for col in range(zone.shape[1]):
                ys = np.where(dark[:, col])[0]
                for a, b in _runs(ys):
                    if b - a + 1 >= min_run:
                        issues.append(f"{name} col={col} y={a}-{b}")
        else:
            for row in range(zone.shape[0]):
                xs = np.where(dark[row, :])[0]
                for a, b in _runs(xs):
                    if b - a + 1 >= min_run:
                        issues.append(f"{name} row={row} x={a}-{b}")

    left_w = max(1, px0)
    check_zone("left", gray[:, :left_w], axis=0)
    right_x = min(w, px1 + 1)
    check_zone("right", gray[:, right_x:], axis=0)
    bottom_y = min(h, py1 + 1)
    check_zone("bottom", gray[bottom_y:, :], axis=1)

    nb = img.max(axis=2) < 40
    left_nb = int(nb[:, :left_w].sum())
    right_nb = int(nb[:, right_x:].sum())
    bottom_nb = int(nb[bottom_y:, :].sum())

    return {
        "clean": len(issues) == 0,
        "issues": issues[:20],
        "near_black_left": left_nb,
        "near_black_right": right_nb,
        "near_black_bottom": bottom_nb,
    }


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
    canvas.save(TMP / "venti1704-margins-white.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    raw = np.array(Image.open(SOURCE).convert("RGB"))
    h, w = raw.shape[:2]
    print(f"source={SOURCE.name} size={w}x{h}")

    cleaned, meta = nuclear_margin_wipe(raw)
    px0, py0, px1, py1 = meta["padded_bbox"]
    print(f"wheel_bbox={meta['wheel_bbox']} padded_bbox={meta['padded_bbox']}")
    print(
        f"outside_whitened={meta['outside_whitened']} "
        f"edge_lines_whitened={meta['edge_lines_whitened']} "
        f"ring_gray_whitened={meta['ring_gray_whitened']}"
    )

    qa = qa_margins(cleaned, px0, py0, px1, py1)
    print(f"QA margins: clean={qa['clean']}")
    print(
        f"near_black left={qa['near_black_left']} right={qa['near_black_right']} "
        f"bottom={qa['near_black_bottom']}"
    )
    if qa["issues"]:
        print(f"issues: {qa['issues']}")
    if not qa["clean"] or qa["near_black_left"] or qa["near_black_right"] or qa["near_black_bottom"]:
        raise SystemExit(f"QA failed: {qa}")

    save_outputs(Image.fromarray(cleaned))
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size} bytes {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size} bytes {Image.open(thumb).size}")
    print("saved public/dist/backend + .tmp-disk/venti1704-margins-white.jpg")


if __name__ == "__main__":
    main()
