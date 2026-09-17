#!/usr/bin/env python3
"""Install Грузовой 17.5 Валдай — remove bottom watermark, face-right as-is."""

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
STEM = "gruzovoy-17-5-valday-gruzovoy-nocolor"
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/"
    "image-c123ced5-0383-4d14-9950-1e41e8aaf8c5.png"
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


def remove_bottom_watermark(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Remove white-outlined «ПЛАНЕТА ЖЕЛЕЗЯКА» across lower face + lip + bg."""
    h, w = img.shape[:2]
    out = img.copy()
    wheel = content_mask(out)
    gray = out.mean(axis=2).astype(np.float32)
    g8 = np.clip(gray, 0, 255).astype(np.uint8)
    ys = np.where(wheel)[0]
    if ys.size == 0:
        return out, 0
    wy1 = int(ys.max())

    # Watermark spans lower face through lip (~y 0.72–0.96) and onto white bg.
    ty0 = int(h * 0.74)
    ty1 = min(h - 1, wy1 + 6)
    zone = np.zeros((h, w), dtype=bool)
    zone[int(h * 0.70) : int(h * 0.96), :] = True

    xs_band = np.where(wheel[ty0 : ty1 + 1].any(axis=0))[0]
    if xs_band.size == 0:
        return out, 0
    x0, x1 = int(xs_band.min()), int(xs_band.max())

    # Stroke / letter-body cues (white outline + semi-transparent fill on silver).
    loc = cv2.GaussianBlur(gray, (0, 0), 2.5)
    hf = np.abs(gray - loc)
    th = cv2.morphologyEx(
        g8, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (17, 9))
    )
    bh = cv2.morphologyEx(
        g8, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (17, 9))
    )
    stroke = zone & wheel & (gray > 95) & ((hf > 2.8) | (th > 11) | (bh > 11))

    wmask = np.zeros((h, w), dtype=np.uint8)
    wmask[ty0 : ty1 + 1, x0 : x1 + 1] = 255
    wmask[~wheel] = 0
    wmask = np.maximum(
        wmask, cv2.dilate(stroke.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 2)
    )
    wmask = cv2.morphologyEx(wmask, cv2.MORPH_CLOSE, np.ones((13, 9), np.uint8), 2)
    wmask[~wheel] = 0
    # Keep deep vent holes as structure donors.
    wmask[gray < 85] = 0

    px = int((wmask > 0).sum())
    if px < 80:
        return out, 0

    # Prefill from clean metal rows above the logo, then TELEA blend.
    yy, xx = np.where(wmask > 0)
    src_y = np.clip(ty0 - 18 - np.maximum(yy - ty0, 0) // 6, 0, ty0 - 1)
    ok = wheel[src_y, xx] & (gray[src_y, xx] > 100)
    out[yy[ok], xx[ok]] = img[src_y[ok], xx[ok]]
    rest = wmask > 0
    rest[yy[ok], xx[ok]] = False
    if rest.any():
        sm = cv2.blur(out, (21, 7))
        out[rest] = sm[rest]
    out = cv2.inpaint(out, wmask, 10, cv2.INPAINT_TELEA)
    sm = cv2.blur(out, (15, 5))
    out[wmask > 0] = sm[wmask > 0]
    out = cv2.inpaint(out, wmask, 5, cv2.INPAINT_TELEA)

    # Residual scrub on / near the repair zone.
    for _ in range(5):
        g2 = out.mean(axis=2).astype(np.float32)
        loc2 = cv2.GaussianBlur(g2, (0, 0), 2.5)
        hf2 = np.abs(g2 - loc2)
        g2u = np.clip(g2, 0, 255).astype(np.uint8)
        bh2 = cv2.morphologyEx(
            g2u, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        )
        th2 = cv2.morphologyEx(
            g2u, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        )
        near = cv2.dilate(wmask, np.ones((21, 21), np.uint8), 1) > 0
        resid = near & wheel & (g2 > 100) & ((hf2 > 3.5) | (bh2 > 8) | (th2 > 8))
        resid |= near & wheel & ((g2 - loc2) > 6) & (g2 > 180)
        count = int(resid.sum())
        if count < 120:
            break
        sm = cv2.blur(out, (13, 3))
        out[resid] = sm[resid]
        ru = cv2.dilate(resid.astype(np.uint8) * 255, np.ones((2, 2), np.uint8), 1)
        out = cv2.inpaint(out, ru, 4, cv2.INPAINT_TELEA)
        px += count

    # Soften bottom lip center (logo often sits on the outer arc).
    lip_y0 = max(ty0, wy1 - 48)
    lip = np.zeros((h, w), dtype=bool)
    lip[lip_y0 : wy1 + 1, x0:x1] = True
    lip &= wheel
    if lip.any():
        med = cv2.medianBlur(out, 15)
        horiz = cv2.blur(out, (25, 1))
        mix = ((med.astype(np.float32) + horiz.astype(np.float32)) / 2.0).astype(np.uint8)
        g3 = out.mean(axis=2).astype(np.float32)
        loc3 = cv2.GaussianBlur(g3, (0, 0), 2.0)
        anom = lip & (np.abs(g3 - loc3) > 2.5)
        out[anom] = mix[anom]
        px += int(anom.sum())

    # Off-wheel bottom: wipe faint outlined logo on white (+ any non-white).
    bg = (np.arange(h)[:, None] >= int(h * 0.70)) & ~wheel
    g4 = out.mean(axis=2)
    g4u = np.clip(g4, 0, 255).astype(np.uint8)
    bh4 = cv2.morphologyEx(
        g4u, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    )
    wipe = bg & ((g4 < 252) | (bh4 > 1))
    wipe = cv2.dilate(wipe.astype(np.uint8) * 255, np.ones((5, 5), np.uint8), 2) > 0
    wipe &= bg
    out[wipe] = (255, 255, 255)
    out[wy1 + 1 :, :] = (255, 255, 255)
    px += int(wipe.sum())

    return out, px


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
    canvas.save(TMP / "valday-17-5-new.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")

    img = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={img.shape[1]}x{img.shape[0]}")

    cleaned, wm_px = remove_bottom_watermark(img)
    print(f"watermark_pixels_inpainted={wm_px}")

    # User source already faces right — do NOT flip
    print("keeping source orientation (face-right, no flip)")

    canvas = fit_canvas(cleaned)
    arr, edge_px = clean_canvas_edge_artifacts(np.array(canvas))
    print(f"canvas_edge_artifacts_whitened={edge_px}")

    save_outputs(Image.fromarray(arr))

    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size}b {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size}b {Image.open(thumb).size}")
    print("saved + .tmp-disk/valday-17-5-new.jpg")


if __name__ == "__main__":
    main()
