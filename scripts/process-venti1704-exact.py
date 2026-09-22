#!/usr/bin/env python3
"""Minimal VENTI 1704 install from user-provided PNG — scale/center only."""

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
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/"
    "image-6fc2ed3d-e52f-4944-a515-5d0e6574b738.png"
)
TW, TH = 900, 1200
FILL = 0.84
MAX_SIDE = int(FILL * min(TW, TH))  # 756


def content_mask(arr: np.ndarray) -> np.ndarray:
    gray = arr.mean(axis=2)
    content = (gray < 245).astype(np.uint8) * 255
    content = cv2.morphologyEx(content, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), 2)
    n, lab, st, _ = cv2.connectedComponentsWithStats(content, 8)
    if n < 2:
        return content > 0
    main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return lab == main


def barrel_on_left(mask: np.ndarray) -> bool:
    ys, xs = np.where(mask)
    cx = xs.mean()
    return (xs < cx).sum() > (xs >= cx).sum()


def fit_canvas(arr: np.ndarray) -> Image.Image:
    h, w = arr.shape[:2]
    scale = MAX_SIDE / max(w, h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = Image.fromarray(arr).resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    canvas.paste(resized, ((TW - nw) // 2, (TH - nh) // 2))
    return canvas


def clean_canvas_edge_artifacts(img: np.ndarray, band: int = 5) -> tuple[np.ndarray, int]:
    """White-out pure black thin L-lines on outer canvas band only."""
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
    canvas.save(TMP / "venti1704-exact.jpg", "JPEG", quality=90, optimize=True)


def save_compare(source: Image.Image, installed: Image.Image) -> None:
    sw, sh = source.size
    scale = 756 / max(sw, sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    src_panel = source.resize((nw, nh), Image.Resampling.LANCZOS)
    src_canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    src_canvas.paste(src_panel, ((TW - nw) // 2, (TH - nh) // 2))
    compare = Image.new("RGB", (TW * 2 + 20, TH), (240, 240, 240))
    compare.paste(src_canvas, (0, 0))
    compare.paste(installed, (TW + 20, 0))
    compare.save(TMP / "venti1704-compare.jpg", "JPEG", quality=90)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")

    source_pil = Image.open(SOURCE).convert("RGB")
    img = np.array(source_pil)
    print(f"source={SOURCE.name} size={img.shape[1]}x{img.shape[0]}")

    mask = content_mask(img)
    barrel_left = barrel_on_left(mask)
    print(f"barrel_on_left={barrel_left} (orientation hint only; no flip — keep original)")

    canvas = fit_canvas(img)
    arr, edge_px = clean_canvas_edge_artifacts(np.array(canvas))
    print(f"canvas_edge_artifacts_whitened={edge_px}")

    final = Image.fromarray(arr)
    save_outputs(final)
    save_compare(source_pil, final)

    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size} bytes {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size} bytes {Image.open(thumb).size}")
    print("saved public/dist/backend + .tmp-disk/venti1704-exact.jpg + venti1704-compare.jpg")


if __name__ == "__main__":
    main()
