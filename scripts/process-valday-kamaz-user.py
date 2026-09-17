#!/usr/bin/env python3
"""Install polished truck rim (black bg → white) for Valdai 17.5 + КамАЗ/МАЗ 8.25."""

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
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/"
    "image-4fe74f2c-cdfb-41ce-b627-c27b9ee8c6ed.png"
)
STEMS = (
    "gruzovoy-17-5-valday-gruzovoy-nocolor",
    "gruzovoy-8-25-22-5-kamaz-maz-gruzovoy-nocolor",
)
TW, TH = 900, 1200
FILL = 0.84
MAX_SIDE = int(FILL * min(TW, TH))  # 756


def wheel_mask_on_black(arr: np.ndarray) -> np.ndarray:
    """Segment bright metal wheel from near-black studio background.

    Vent / hub holes stay open (False) so studio black becomes white on canvas.
    """
    gray = arr.mean(axis=2)
    # Soft threshold — keep shadowed metal, drop pure black
    content = (gray > 22).astype(np.uint8) * 255
    # Mild close to join metal without sealing large vent holes
    content = cv2.morphologyEx(content, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), 1)
    content = cv2.morphologyEx(content, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), 1)
    n, lab, st, _ = cv2.connectedComponentsWithStats(content, 8)
    if n < 2:
        return content > 0
    main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    mask = lab == main
    # Drop tiny speckles that aren't part of the main metal body
    return mask


def silhouette_bbox_mask(mask: np.ndarray) -> np.ndarray:
    """Filled outline for crop bounds only (holes ignored for bbox)."""
    m8 = (mask.astype(np.uint8) * 255)
    inv = cv2.bitwise_not(m8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 8)
    filled = mask.copy()
    if n2 >= 2:
        exterior = 1 + int(np.argmax(st2[1:, cv2.CC_STAT_AREA]))
        holes = (lab2 > 0) & (lab2 != exterior)
        filled = filled | holes
    return filled


def to_white_bg(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    # Stronger erode drops dark AA fringe on outer lip + hole rims; soft feather
    m8 = (mask.astype(np.uint8) * 255)
    m8 = cv2.erode(m8, np.ones((5, 5), np.uint8), iterations=2)
    m8 = cv2.GaussianBlur(m8, (11, 11), 0)
    alpha = (m8.astype(np.float32) / 255.0)[..., None]
    white = np.full_like(arr, 255, dtype=np.float32)
    blended = arr.astype(np.float32) * alpha + white * (1.0 - alpha)
    out = np.clip(blended, 0, 255).astype(np.uint8)
    # Kill residual dark halo next to pure white (outer + vent holes)
    gray = out.mean(axis=2)
    near_white = cv2.dilate((gray > 248).astype(np.uint8), np.ones((5, 5), np.uint8), 1)
    halo = (near_white > 0) & (gray < 160)
    if halo.any():
        a = np.clip((gray[halo] - 40.0) / 120.0, 0.0, 1.0)[..., None]
        out[halo] = (
            out[halo].astype(np.float32) * a + 255.0 * (1.0 - a)
        ).astype(np.uint8)
    return out


def fit_canvas(arr: np.ndarray, mask: np.ndarray) -> Image.Image:
    bbox = silhouette_bbox_mask(mask)
    ys, xs = np.where(bbox)
    pad = 12
    x0, x1 = max(0, int(xs.min()) - pad), min(arr.shape[1], int(xs.max()) + pad + 1)
    y0, y1 = max(0, int(ys.min()) - pad), min(arr.shape[0], int(ys.max()) + pad + 1)
    crop = arr[y0:y1, x0:x1]
    h, w = crop.shape[:2]
    scale = MAX_SIDE / max(w, h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = Image.fromarray(crop).resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    x = (TW - nw) // 2
    y = (TH - nh) // 2
    canvas.paste(resized, (x, y))
    return canvas


def clean_canvas_edge_artifacts(img: np.ndarray, band: int = 5) -> tuple[np.ndarray, int]:
    h, w = img.shape[:2]
    out = img.copy()
    maxc = out.max(axis=2)
    gray = out.mean(axis=2)
    edge = np.zeros((h, w), dtype=bool)
    edge[:band, :] = True
    edge[h - band :, :] = True
    edge[:, :band] = True
    edge[:, w - band :] = True
    local = cv2.GaussianBlur(gray.astype(np.float32), (7, 7), 0)
    artifact = edge & (maxc < 120) & (local > 200)
    count = int(artifact.sum())
    if count:
        out[artifact] = (255, 255, 255)
    # Exterior-only halo: grow pure-white exterior into soft dark fringe, leave metal
    exterior = (gray > 252).astype(np.uint8)
    # Flood from corners so we only expand true background, not white highlights on metal
    flood = exterior.copy()
    for cy, cx in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if flood[cy, cx]:
            cv2.floodFill(flood, None, (cx, cy), 2)
    bg = flood == 2
    ring = cv2.dilate(bg.astype(np.uint8), np.ones((9, 9), np.uint8), 2) > 0
    # Soft gray/black leftover hugging white bg (incl. faint drop-shadow)
    halo = ring & ~bg & (gray < 210)
    hc = int(halo.sum())
    if hc:
        # Blend toward white by darkness — darkest fully white
        a = np.clip((gray[halo] - 80.0) / 130.0, 0.0, 1.0)[..., None]
        out[halo] = (out[halo].astype(np.float32) * a + 255.0 * (1.0 - a)).astype(np.uint8)
        # Force very dark fringe fully white
        hard = halo & (gray < 120)
        out[hard] = (255, 255, 255)
        count += hc
    return out, count


def save_outputs(canvas: Image.Image) -> None:
    for d in (PUBLIC, DIST, BACKEND):
        d.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for stem in STEMS:
        full = PUBLIC / f"{stem}.jpg"
        thumb = PUBLIC / f"{stem}-thumb.jpg"
        canvas.save(full, "JPEG", quality=90, optimize=True)
        thimg = canvas.copy()
        thimg.thumbnail((360, 480), Image.Resampling.LANCZOS)
        thimg.save(thumb, "JPEG", quality=85, optimize=True)
        for d in (DIST, BACKEND):
            shutil.copy2(full, d / f"{stem}.jpg")
            shutil.copy2(thumb, d / f"{stem}-thumb.jpg")
    canvas.save(TMP / "valday-kamaz-new.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")

    img = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={img.shape[1]}x{img.shape[0]}")

    mask = wheel_mask_on_black(img)
    print(f"mask_pixels={int(mask.sum())}")
    print("keeping source orientation (face-right, no flip)")

    white = to_white_bg(img, mask)
    canvas = fit_canvas(white, mask)
    arr, edge_px = clean_canvas_edge_artifacts(np.array(canvas))
    print(f"canvas_edge_artifacts_whitened={edge_px}")

    save_outputs(Image.fromarray(arr))
    for stem in STEMS:
        full = PUBLIC / f"{stem}.jpg"
        thumb = PUBLIC / f"{stem}-thumb.jpg"
        print(
            f"{stem}: full={full.stat().st_size}b {Image.open(full).size} "
            f"thumb={thumb.stat().st_size}b"
        )
    print("saved + .tmp-disk/valday-kamaz-new.jpg")


if __name__ == "__main__":
    main()
