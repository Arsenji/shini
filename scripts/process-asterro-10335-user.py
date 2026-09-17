#!/usr/bin/env python3
"""Gentle Asterro 10-335-281-135 install — no silhouette cutout."""

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
STEM = "asterro-10-335-281-135-gruzovoy-nocolor"
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/"
    "image-6f094c9b-0cdc-4f39-a7e4-15fc4632847a.png"
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
    return out, count


def qa_gentle(img: np.ndarray) -> dict:
    h, w = img.shape[:2]
    mask = content_mask(img)
    maxc = img.max(axis=2)
    issues: list[str] = []

    if (w, h) != (TW, TH):
        issues.append(f"size={w}x{h}")

    barrel_left = barrel_on_left(mask)
    if not barrel_left:
        issues.append("orientation: barrel not on left (face should point right)")

    band = 5
    edge = np.zeros((h, w), dtype=bool)
    edge[:band, :] = True
    edge[h - band :, :] = True
    edge[:, :band] = True
    edge[:, w - band :] = True
    edge_dark = int((edge & (maxc < 80)).sum())
    if edge_dark > 20:
        issues.append(f"edge_band_dark_px={edge_dark}")

    return {
        "clean": len(issues) == 0,
        "issues": issues,
        "barrel_on_left": barrel_left,
        "edge_band_dark_px": edge_dark,
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
    canvas.save(TMP / "asterro-10335-new.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")

    img = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={img.shape[1]}x{img.shape[0]}")

    mask = content_mask(img)
    barrel_left = barrel_on_left(mask)
    print(f"barrel_on_left={barrel_left} (True=face-right, no flip needed)")

    # User confirmed already faces right — do NOT flip
    if not barrel_left:
        print("WARNING: barrel not on left but user said no flip — keeping as-is")

    canvas = fit_canvas(img)
    arr, edge_px = clean_canvas_edge_artifacts(np.array(canvas))
    print(f"canvas_edge_artifacts_whitened={edge_px}")

    qa = qa_gentle(arr)
    print(f"QA: {qa}")

    save_outputs(Image.fromarray(arr))

    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size} bytes {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size} bytes {Image.open(thumb).size}")
    print("saved public/dist/backend + .tmp-disk/asterro-10335-new.jpg")


if __name__ == "__main__":
    main()
