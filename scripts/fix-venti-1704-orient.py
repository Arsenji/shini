#!/usr/bin/env python3
"""VENTI 1704: nuclear shinservice dewatermark (attempt 1) or black-diamond swap (attempt 2)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/wheels"
DIST = ROOT / "dist/wheels"
BACKEND = ROOT / "backend/static/wheels"
TMP = ROOT / ".tmp-disk"
STEM = "venti-1704-66-1-litoy-chernyy-almaz"
FALLBACK_STEM = "wheel-litoy-black-diamond"
SOURCE = TMP / "venti1704-shinservice.jpg"
SOURCE_URL = "https://s1.shinservice.ru/catalog/disk/venti/huge/1704.bfp.jpg"
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


def face_right(arr: np.ndarray) -> np.ndarray:
    """Catalog wheels face right (barrel on left side of silhouette mass)."""
    mask = content_mask(arr)
    if barrel_on_left(mask):
        return cv2.flip(arr, 1)
    return arr


def _logo_mask(hsv: np.ndarray) -> np.ndarray:
    red = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 90, 90]), np.array([12, 255, 255])),
        cv2.inRange(hsv, np.array([168, 90, 90]), np.array([180, 255, 255])),
    )
    red_loose = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 40, 60]), np.array([15, 255, 255])),
        cv2.inRange(hsv, np.array([165, 40, 60]), np.array([180, 255, 255])),
    )
    blue = cv2.inRange(hsv, np.array([100, 70, 55]), np.array([130, 255, 210]))
    return cv2.morphologyEx(
        cv2.bitwise_or(red, cv2.bitwise_or(red_loose, blue)),
        cv2.MORPH_DILATE,
        np.ones((3, 3), np.uint8),
        1,
    )


def _red_rgb_mask(band: np.ndarray) -> np.ndarray:
    r, g, b = band[:, :, 0], band[:, :, 1], band[:, :, 2]
    return (r.astype(int) > g + 22) & (r.astype(int) > b + 22) & (r > 95)


def _text_edge_mask(gray: np.ndarray) -> np.ndarray:
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    edges = mag > 28
    edges = cv2.morphologyEx(edges.astype(np.uint8) * 255, cv2.MORPH_DILATE, np.ones((2, 2), np.uint8), 1) > 0
    return edges & (gray > 120) & (gray < 245)


def _nuclear_watermark_mask(img: np.ndarray, wheel: np.ndarray, y0: int) -> np.ndarray:
    """Bottom 35%: semi-white overlay, logo colors, or text-like edges."""
    h, w = img.shape[:2]
    band = img[y0:h, :, :]
    gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(band, cv2.COLOR_BGR2HSV)
    local = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), 7)

    logo = _logo_mask(hsv) > 0
    red = _red_rgb_mask(band)
    blue = cv2.inRange(hsv, np.array([100, 60, 45]), np.array([135, 255, 220])) > 0

    semi_white = (gray > 175) & (gray < 253) & (hsv[:, :, 1] < 65) & ((gray.astype(np.float32) - local) > 6)
    semi_white = cv2.morphologyEx(semi_white.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), 1) > 0

    textish = _text_edge_mask(gray) & (hsv[:, :, 1] < 120)
    logo_zone = cv2.dilate(logo.astype(np.uint8) * 255, np.ones((21, 21), np.uint8), 2) > 0

    wm_band = logo | red | (blue & logo_zone) | semi_white | (textish & (semi_white | logo_zone))
    wm_band = cv2.morphologyEx(wm_band.astype(np.uint8) * 255, cv2.MORPH_DILATE, np.ones((3, 3), np.uint8), 1) > 0

    wm = np.zeros((h, w), bool)
    wm[y0:h, :] = wm_band

    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    local_full = cv2.GaussianBlur(gray_full, (0, 0), 9)
    hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    washed_band = (
        (gray_full[y0:h, :] > 168)
        & (gray_full[y0:h, :] < 252)
        & (hsv_full[y0:h, :, 1] < 72)
        & ((gray_full[y0:h, :] - local_full[y0:h, :]) > 8)
    )
    wm[y0:h, :] |= washed_band & (wm_band | (gray > 170))

    return wm


def _hub_mask(wheel: np.ndarray) -> np.ndarray:
    ys, xs = np.where(wheel)
    cy, cx = int(ys.mean()), int(xs.mean())
    y0, y1 = ys.min(), ys.max()
    r = int((y1 - y0) * 0.17)
    yy, xx = np.ogrid[: wheel.shape[0], : wheel.shape[1]]
    return ((yy - cy) ** 2 + (xx - cx) ** 2) <= r * r


def _donor_from_flip(out: np.ndarray, wheel: np.ndarray, repair: np.ndarray) -> np.ndarray:
    """Replace repair pixels with horizontally mirrored clean donor pixels."""
    if not repair.any():
        return out
    result = out.copy()
    flipped = cv2.flip(result, 1)
    remaining = repair.copy()
    ry, rx = np.where(repair)
    fx = (out.shape[1] - 1 - rx).astype(np.int32)
    donor_ok = wheel[ry, fx] & ~repair[ry, fx]
    result[ry[donor_ok], rx[donor_ok]] = flipped[ry[donor_ok], rx[donor_ok]]
    remaining[ry[donor_ok], rx[donor_ok]] = False
    return result, remaining


def nuclear_clean_source(img: np.ndarray) -> np.ndarray:
    """Attempt 1: aggressive bottom-35% watermark strip on shinservice source."""
    h, w = img.shape[:2]
    wheel = content_mask(img)
    hub = _hub_mask(wheel)
    y0 = int(h * 0.65)
    wm = _nuclear_watermark_mask(img, wheel, y0)
    out = img.copy()

    # Step 3: outside wheel silhouette in bottom band → pure white
    bottom = np.zeros((h, w), bool)
    bottom[y0:h, :] = True
    out[bottom & ~wheel] = (255, 255, 255)

    # Step 4: watermark on wheel → TELEA r=12, then mirror donor
    on_wheel = wm & wheel & ~hub
    if on_wheel.any():
        inpaint_mask = cv2.dilate(on_wheel.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 1)
        out = cv2.inpaint(out, inpaint_mask, 12, cv2.INPAINT_TELEA)
        out, remaining = _donor_from_flip(out, wheel, on_wheel.copy())
        if remaining.any():
            full = cv2.morphologyEx(remaining.astype(np.uint8) * 255, cv2.MORPH_DILATE, np.ones((2, 2), np.uint8), 1)
            out = cv2.inpaint(out, full, 8, cv2.INPAINT_TELEA)

    # Second pass for lingering washed pixels on lower spokes
    gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32)
    local = cv2.GaussianBlur(gray, (0, 0), 9)
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
    linger = (
        bottom
        & wheel
        & ~hub
        & (gray > 165)
        & (gray < 250)
        & (hsv[:, :, 1] < 55)
        & ((gray - local) > 10)
    )
    if linger.any():
        inpaint_mask = cv2.dilate(linger.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 1)
        out = cv2.inpaint(out, inpaint_mask, 10, cv2.INPAINT_TELEA)
        out, _ = _donor_from_flip(out, wheel, linger)

    return out


def scrub_canvas_background(img: np.ndarray) -> np.ndarray:
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
    y = max(40, min(TH - nh - 80, int((TH - nh) * 0.35)))
    canvas.paste(crop, (x, y))
    return canvas


def _watermark_probe_zone(h: int, w: int, face_right: bool) -> np.ndarray:
    """Bottom 35% band; shinservice banner sits on the trailing corner."""
    zone = np.zeros((h, w), bool)
    zone[int(h * 0.65) :, :] = True
    if face_right:
        zone[:, : int(w * 0.55)] = False
    else:
        zone[:, int(w * 0.45) :] = False
    return zone


def qa_shinservice_watermark(arr: np.ndarray) -> dict[str, object]:
    """Detect shinservice banner ghosts / logo colors on lower spokes."""
    mask = content_mask(arr)
    hub = _hub_mask(mask)
    h, w = arr.shape[:2]
    facing_right = not barrel_on_left(mask)
    zone = _watermark_probe_zone(h, w, facing_right)

    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    local = cv2.GaussianBlur(gray, (0, 0), 11)
    hsv = cv2.cvtColor(arr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]

    blotch = (
        zone
        & mask
        & ~hub
        & (gray > 190)
        & (gray < 248)
        & (sat < 42)
        & ((gray - local) > 14)
    )

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    red_logo = zone & mask & ~hub & (r > 120) & (r.astype(int) > g + 35) & (r.astype(int) > b + 35) & (sat > 70)
    blue_logo = zone & mask & ~hub & (cv2.inRange(hsv, np.array([98, 90, 70]), np.array([128, 255, 210])) > 0)

    dirty = blotch | red_logo | blue_logo
    return {
        "face_right": facing_right,
        "blotch_pixels": int(blotch.sum()),
        "red_pixels": int(red_logo.sum()),
        "blue_pixels": int(blue_logo.sum()),
        "dirty_pixels": int(dirty.sum()),
        "dirty": int(blotch.sum()) > 600 or int(red_logo.sum()) > 80 or int(blue_logo.sum()) > 80,
    }


def save_outputs(canvas: Image.Image, qa_name: str = "venti1704-done.jpg") -> None:
    for d in (PUBLIC, DIST, BACKEND):
        d.mkdir(parents=True, exist_ok=True)
    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    canvas.save(full, "JPEG", quality=90, optimize=True)
    thimg = canvas.copy()
    thimg.thumbnail((360, 480))
    thimg.save(thumb, "JPEG", quality=85, optimize=True)
    for d in (DIST, BACKEND):
        (d / f"{STEM}.jpg").write_bytes(full.read_bytes())
        (d / f"{STEM}-thumb.jpg").write_bytes(thumb.read_bytes())
    TMP.mkdir(parents=True, exist_ok=True)
    canvas.save(TMP / "venti1704-ok.jpg", "JPEG", quality=90, optimize=True)
    canvas.save(TMP / qa_name, "JPEG", quality=90, optimize=True)


def attempt2_fallback() -> Image.Image:
    """Copy clean black-diamond generic wheel (already face-right)."""
    src = PUBLIC / f"{FALLBACK_STEM}.jpg"
    if not src.exists():
        raise SystemExit(f"missing fallback source: {src}")
    return Image.open(src).convert("RGB")


def ensure_source() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    if SOURCE.exists() and SOURCE.stat().st_size > 10000:
        return
    subprocess.check_call(
        ["curl", "-sL", "--fail", "-o", str(SOURCE), SOURCE_URL],
        timeout=30,
    )


def main() -> None:
    ensure_source()
    raw = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} barrel_on_left={barrel_on_left(content_mask(raw))}")

    attempt = 1
    cleaned = nuclear_clean_source(raw)
    oriented = face_right(cleaned)
    if barrel_on_left(content_mask(oriented)):
        raise SystemExit("orientation wrong: expected face-right (barrel_on_left=False)")

    canvas = fit_canvas(oriented)
    arr = scrub_canvas_background(np.array(canvas))
    report = qa_shinservice_watermark(arr)
    print(f"Attempt 1 QA: {report}")

    if report["dirty"]:
        attempt = 2
        print("Attempt 1 still dirty → using wheel-litoy-black-diamond fallback")
        canvas = attempt2_fallback()
        arr = np.array(canvas)
        report = qa_shinservice_watermark(arr)
        print(f"Attempt 2 QA: {report}")
        if not report["face_right"]:
            raise SystemExit(f"Attempt 2 orientation wrong: {report}")
        if report["dirty"]:
            raise SystemExit(f"Attempt 2 still has watermark signature: {report}")

    save_outputs(Image.fromarray(arr))
    print(f"USED ATTEMPT {attempt}")
    print("saved public/dist/backend + .tmp-disk/venti1704-ok.jpg + venti1704-done.jpg")


if __name__ == "__main__":
    main()
