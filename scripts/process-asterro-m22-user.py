#!/usr/bin/env python3
"""Install new Asterro M22 user photo — remove left-side logo watermark, no flip."""

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
STEM = "asterro-m22-gruzovoy-nocolor"
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/"
    "image-d42bb5a2-db00-41ac-a535-c6286a9da403.png"
)
TW, TH = 900, 1200
FILL = 0.84
MAX_SIDE = int(FILL * min(TW, TH))  # 756
UPSCALE = 3


def content_mask(arr: np.ndarray) -> np.ndarray:
    gray = arr.mean(axis=2)
    content = (gray < 245).astype(np.uint8) * 255
    content = cv2.morphologyEx(content, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), 2)
    n, lab, st, _ = cv2.connectedComponentsWithStats(content, 8)
    if n < 2:
        return content > 0
    main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return lab == main


def remove_left_logo_watermark(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Remove grey curved logo on left barrel.

    Logo is near-neutral grey (almost no RGB contrast), so edge/contrast masks
    miss it. Use a solid left-barrel annulus mask, copy clean metal from the
    right along each row at 3× scale, then TELEA+NS inpaint.
    """
    h0, w0 = img.shape[:2]
    S = UPSCALE
    work = cv2.resize(img, (w0 * S, h0 * S), interpolation=cv2.INTER_CUBIC)
    h, w = work.shape[:2]
    gray = work.mean(axis=2).astype(np.float32)
    wheel = content_mask(work)

    yy, xx = np.mgrid[0:h, 0:w]
    ocx, ocy = 160.0 * S, 175.0 * S
    r = np.sqrt((xx - ocx) ** 2 + (yy - ocy) ** 2)

    mask = (
        wheel
        & (xx >= int(18 * S))
        & (xx <= int(135 * S))
        & (yy >= int(40 * S))
        & (yy <= int(310 * S))
        & (r >= int(75 * S))
        & (r <= int(168 * S))
        & (gray > 80)
        & (gray < 242)
    ).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8), 2)
    mask[gray < 55] = 0

    if int((mask > 0).sum()) < 50:
        return img, 0

    out = work.copy()
    yy_m, xx_m = np.where(mask > 0)
    donor_x = np.full(h, -1, dtype=np.int32)
    for y in range(h):
        row = mask[y] > 0
        if not row.any():
            continue
        x_end = int(np.where(row)[0].max())
        for x in range(x_end + 1, min(w, x_end + 120 * S)):
            if wheel[y, x] and mask[y, x] == 0 and 110 < gray[y, x] < 230:
                donor_x[y] = x
                break

    for y, x in zip(yy_m, xx_m):
        y, x = int(y), int(x)
        dx = donor_x[y]
        if dx >= 0:
            out[y, x] = work[y, dx]
            continue
        for dy in (1, -1, 2, -2, 3, -3):
            y2 = y + dy
            if 0 <= y2 < h and donor_x[y2] >= 0:
                out[y, x] = work[y2, donor_x[y2]]
                break

    out = cv2.inpaint(out, mask, 12, cv2.INPAINT_TELEA)
    out = cv2.inpaint(out, mask, 8, cv2.INPAINT_NS)

    sm = cv2.bilateralFilter(out, 9, 40, 40)
    alpha = (cv2.GaussianBlur(mask.astype(np.float32), (31, 31), 0) / 255.0)[..., None]
    out = (
        out.astype(np.float32) * (1.0 - alpha * 0.7)
        + sm.astype(np.float32) * (alpha * 0.7)
    ).astype(np.uint8)

    final = cv2.resize(out, (w0, h0), interpolation=cv2.INTER_AREA)

    # Soft repair only extreme blown lip pixels (keep silver brighter than
    # logo-darkened source — that is expected after watermark removal).
    g = final.mean(axis=2).astype(np.float32)
    wheel0 = content_mask(final)
    washed = wheel0 & (g > 248) & (np.arange(w0)[None, :] < 70)
    if washed.any():
        wu = cv2.dilate(washed.astype(np.uint8) * 255, np.ones((2, 2), np.uint8), 1)
        yy, xx = np.where(wu > 0)
        for y, x in zip(yy, xx):
            for dx in range(3, 45):
                x2 = x + dx
                if x2 >= w0:
                    break
                if wheel0[y, x2] and 120 < g[y, x2] < 230:
                    final[y, x] = final[y, x2]
                    break
        final = cv2.inpaint(final, wu, 3, cv2.INPAINT_TELEA)

    mask0 = cv2.resize(mask, (w0, h0), interpolation=cv2.INTER_NEAREST)
    return final, int((mask0 > 0).sum())


def fit_canvas(arr: np.ndarray, lift: float = 0.04) -> Image.Image:
    """Center on canvas; slight upward bias like prior M22 compose."""
    h, w = arr.shape[:2]
    scale = MAX_SIDE / max(w, h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = Image.fromarray(arr).resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    x = (TW - nw) // 2
    y = (TH - nh) // 2 - int(TH * lift)
    y = max(20, min(y, TH - nh - 20))
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


def save_outputs(canvas: Image.Image) -> None:
    for d in (PUBLIC, DIST, BACKEND):
        d.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    canvas.save(full, "JPEG", quality=90, optimize=True)
    thimg = canvas.copy()
    thimg.thumbnail((360, 480), Image.Resampling.LANCZOS)
    thimg.save(thumb, "JPEG", quality=85, optimize=True)
    for d in (DIST, BACKEND):
        shutil.copy2(full, d / f"{STEM}.jpg")
        shutil.copy2(thumb, d / f"{STEM}-thumb.jpg")
    canvas.save(TMP / "asterro-m22-new.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")

    img = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={img.shape[1]}x{img.shape[0]}")

    cleaned, wm_px = remove_left_logo_watermark(img)
    print(f"watermark_pixels_inpainted={wm_px}")
    print("keeping source orientation (face-right, no flip)")

    canvas = fit_canvas(cleaned)
    arr, edge_px = clean_canvas_edge_artifacts(np.array(canvas))
    print(f"canvas_edge_artifacts_whitened={edge_px}")

    save_outputs(Image.fromarray(arr))
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size}b {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size}b {Image.open(thumb).size}")
    print("saved + .tmp-disk/asterro-m22-new.jpg")


if __name__ == "__main__":
    main()
