#!/usr/bin/env python3
"""Install Грузовой 5 SRW (Газон NEXT) — remove DROM watermark, face-right."""

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
STEM = "gruzovoy-5-srw-gazon-next-gruzovoy-nocolor"
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/"
    "image-86fef619-4a04-47cd-8563-6bb06fac8050.png"
)
TW, TH = 900, 1200
FILL = 0.84
MAX_SIDE = int(FILL * min(TW, TH))
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


def _letter_mask(gray: np.ndarray, wheel: np.ndarray, loose: bool = False) -> np.ndarray:
    """Detect «ДРОМ» glyphs in mid band 35–65% (keep7-style, letter-shaped)."""
    h, w = gray.shape
    scale = max(h, w) / 432.0
    s_med = max(3.0, 8.0 * scale)
    s_large = max(12.0, 35.0 * scale)
    med = cv2.GaussianBlur(gray, (0, 0), s_med)
    large = cv2.GaussianBlur(gray, (0, 0), s_large)
    res = med - large
    # Positive excess vs larger blur (light translucent overlay)
    excess = gray - cv2.GaussianBlur(gray, (0, 0), max(20.0, 40.0 * scale))

    sx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    edge = np.sqrt(sx * sx + sy * sy)

    zone = np.zeros((h, w), dtype=bool)
    zone[int(h * 0.35) : int(h * 0.65), int(w * 0.04) : int(w * 0.96)] = True
    metal = wheel & (gray > 85) & (gray < 240)

    # Aggressive light-overlay detect, but keep letter-like (low edge)
    lo_res = 1.8 if loose else 2.3
    hi_res = 16.0 if loose else 14.0
    lo_ex = 0.9 if loose else 1.3
    edge_thr = (50.0 if loose else 45.0) * scale**0.3
    cand = zone & metal & (edge < edge_thr) & (
        ((np.abs(res) > lo_res * scale**0.3) & (np.abs(res) < hi_res * scale**0.3))
        | (excess > lo_ex)
    )

    m = cand.astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 5), np.uint8), 2)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros((h, w), dtype=np.uint8)
    min_area = max(60, int(60 * scale * scale))
    min_bw = max(8, int(8 * scale))
    max_area = h * w // 4
    for i in range(1, n):
        area = int(st[i, cv2.CC_STAT_AREA])
        bw = int(st[i, cv2.CC_STAT_WIDTH])
        bh = int(st[i, cv2.CC_STAT_HEIGHT])
        if area < min_area or area > max_area or bw < min_bw:
            continue
        # Prefer wide glyph blobs; drop full-height thin walls
        if bh > 0.9 * (int(h * 0.65) - int(h * 0.35)) and bw < 14 * scale:
            continue
        keep[lab == i] = 255

    # Solidify glyphs moderately (keep7: close 9x13 ×3, dilate 4×2)
    kc1 = max(7, int(round(9 * scale)))
    kc2 = max(11, int(round(13 * scale)))
    if kc1 % 2 == 0:
        kc1 += 1
    if kc2 % 2 == 0:
        kc2 += 1
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((kc1, kc2), np.uint8), 3)
    kd = max(3, int(round(4 * scale)))
    if kd % 2 == 0:
        kd += 1
    keep = cv2.dilate(keep, np.ones((kd, kd), np.uint8), 2)
    # Halo for soft translucent letter edges
    if loose:
        keep = cv2.dilate(keep, np.ones((kd, kd), np.uint8), 1)

    keep[gray < 50] = 0
    keep[edge > 95 * scale**0.3] = 0

    # Protect stamped markings
    hf = np.abs(gray - cv2.GaussianBlur(gray, (0, 0), max(1.0, 1.4 * scale)))
    stamp = ((hf > 5.5) & (edge > 22) & (edge < 85)).astype(np.uint8) * 255
    stamp = cv2.morphologyEx(stamp, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), 1)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(stamp, 8)
    for i in range(1, n2):
        a = int(st2[i, cv2.CC_STAT_AREA])
        if 6 <= a <= int(350 * scale * scale):
            keep[lab2 == i] = 0

    return keep


def remove_drom_watermark(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Remove faint semi-transparent «ДРОМ» across mid face.

    Letter-shaped mid-band mask (35–65%). Multi-pass: lightening undo +
    band-pass undo + small-radius TELEA on residual cores until ghost text
    energy is gone. Avoids solid mid-band TELEA that smudges silver metal.
    """
    h0, w0 = img.shape[:2]
    S = UPSCALE
    work = cv2.resize(img, (w0 * S, h0 * S), interpolation=cv2.INTER_CUBIC)
    h, w = work.shape[:2]
    wheel = content_mask(work)
    scale = max(h, w) / 432.0
    out = work.astype(np.float32)
    total_px = 0

    for pass_i in range(6):
        gray = out.mean(axis=2)
        keep = _letter_mask(gray, wheel, loose=(pass_i >= 2))
        px = int((keep > 0).sum())
        if px < 80:
            break

        # Cap mask size — letter glyphs, not whole mid band
        zone = np.zeros((h, w), dtype=bool)
        zone[int(h * 0.35) : int(h * 0.65)] = True
        mid_metal = int((zone & wheel & (gray > 85) & (gray < 240)).sum())
        if mid_metal > 0 and px > 0.45 * mid_metal:
            keep = cv2.erode(keep, np.ones((5, 5), np.uint8), 1)
            px = int((keep > 0).sum())
            if px < 80:
                break

        total_px += px
        soft = (
            cv2.GaussianBlur(keep.astype(np.float32), (0, 0), max(0.8, 1.1 * scale))
            / 255.0
        )
        a = soft[..., None]

        # Lightening undo (moderate — avoid dark mid-band smudge)
        ex_gain = 1.55 if pass_i == 0 else 1.25
        bg = cv2.GaussianBlur(out, (0, 0), 35.0 * scale)
        pos = np.maximum(out - bg, 0.0)
        out = np.clip(out - ex_gain * a * pos, 0, 255)

        # Band-pass undo
        bp_gain = 2.4 if pass_i == 0 else (1.9 if pass_i < 3 else 1.5)
        for sm, sl in ((8.0, 35.0), (14.0, 60.0)):
            band = cv2.GaussianBlur(out, (0, 0), sm * scale) - cv2.GaussianBlur(
                out, (0, 0), sl * scale
            )
            out = np.clip(out - bp_gain * a * band, 0, 255)

        out_u8 = np.clip(out, 0, 255).astype(np.uint8)
        g2 = out_u8.mean(axis=2).astype(np.float32)
        sx = cv2.Sobel(g2, cv2.CV_32F, 1, 0, ksize=3)
        sy = cv2.Sobel(g2, cv2.CV_32F, 0, 1, ksize=3)
        edge = np.sqrt(sx * sx + sy * sy)
        res2 = cv2.GaussianBlur(g2, (0, 0), 8.0 * scale) - cv2.GaussianBlur(
            g2, (0, 0), 35.0 * scale
        )
        ex2 = g2 - cv2.GaussianBlur(g2, (0, 0), 35.0 * scale)

        # TELEA only on residual letter cores (small), then seams
        thr_ex = 1.8 if pass_i < 2 else 1.3
        thr_res = 2.4 if pass_i < 2 else 1.8
        core = (
            (keep > 0)
            & (edge < 48.0 * scale**0.3)
            & ((ex2 > thr_ex) | ((np.abs(res2) > thr_res) & (np.abs(res2) < 12)))
        )
        telea = cv2.dilate(core.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 1)
        telea[edge > 100 * scale**0.3] = 0
        if int(telea.sum()) > 0:
            out_u8 = cv2.inpaint(out_u8, telea, 3, cv2.INPAINT_TELEA)
            out_u8 = cv2.inpaint(out_u8, telea, 2, cv2.INPAINT_TELEA)

        seam = ((soft > 0.12) & (soft < 0.65)).astype(np.uint8) * 255
        seam[edge > 95 * scale**0.3] = 0
        if int(seam.sum()) > 0:
            out_u8 = cv2.inpaint(out_u8, seam, 2, cv2.INPAINT_TELEA)

        out = out_u8.astype(np.float32)
        rem = float(np.maximum(ex2, 0.0)[keep > 0].mean()) if px else 0.0
        if rem < 1.1 and pass_i >= 1:
            break

    final = cv2.resize(
        np.clip(out, 0, 255).astype(np.uint8), (w0, h0), interpolation=cv2.INTER_AREA
    )
    return final, total_px


def fit_canvas(arr: np.ndarray) -> Image.Image:
    mask = content_mask(arr)
    ys, xs = np.where(mask)
    pad = 10
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
    canvas.save(TMP / "gazon-5srw-new.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")
    img = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={img.shape[1]}x{img.shape[0]}")
    print("keeping source orientation (face-right, no flip)")
    cleaned, wm_px = remove_drom_watermark(img)
    print(f"watermark_pixels_inpainted={wm_px}")
    canvas = fit_canvas(cleaned)
    arr, edge_px = clean_canvas_edge_artifacts(np.array(canvas))
    print(f"canvas_edge_artifacts_whitened={edge_px}")
    save_outputs(Image.fromarray(arr))
    full = PUBLIC / f"{STEM}.jpg"
    print(f"full={full.stat().st_size}b {Image.open(full).size}")
    print("saved + .tmp-disk/gazon-5srw-new.jpg")


if __name__ == "__main__":
    main()
