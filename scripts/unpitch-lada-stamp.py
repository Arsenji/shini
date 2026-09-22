#!/usr/bin/env python3
"""Perspective-unpitch tzsk-lada-4x4-shtamp-nocolor — strong bbox warp."""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/wheels"
DIST = ROOT / "dist/wheels"
BACKEND = ROOT / "backend/static/wheels"
TMP = ROOT / ".tmp-disk"
STEM = "tzsk-lada-4x4-shtamp-nocolor"
REF_PATH = PUBLIC / "wheel-shtamp-black.jpg"

TW, TH, FILL = 900, 1200, 0.84
UPSCALE_LONG = 1600

# 3/4-view raw (face-right) sources; mosa max is face-on and not suitable for orientation
SOURCE_CANDIDATES = [
    TMP / "tzsk-lada-4x4-shtamp-nocolor-raw.bin",
    TMP / "lada-raw.jpg",
    TMP / "tzsk-lada-raw.jpg",
]


def load_rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


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


def clean_on_white(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    gray = arr.mean(axis=2)
    pad = cv2.dilate(mask.astype(np.uint8) * 255, np.ones((5, 5), np.uint8), 2) > 0
    out = arr.copy()
    out[~pad] = (255, 255, 255)
    soft = (gray > 200) & (gray < 250) & ~pad
    out[soft] = (255, 255, 255)
    return out


def fit_outer_ellipse(mask: np.ndarray):
    pts = cv2.findNonZero(mask.astype(np.uint8) * 255)
    if pts is None or len(pts) < 5:
        raise ValueError("not enough contour points")
    return cv2.fitEllipse(pts)


def face_vertical_ratio(ellipse) -> float:
    (_, _), (ma, mi), ang = ellipse
    rad = math.radians(ang)
    vy = abs(ma / 2 * math.sin(rad)) + abs(mi / 2 * math.cos(rad))
    vx = abs(ma / 2 * math.cos(rad)) + abs(mi / 2 * math.sin(rad))
    return (2 * vy) / max(2 * vx, 1e-6)


def top_bottom_width_ratio(mask: np.ndarray) -> float:
    ys, xs = np.where(mask)
    y0, y1 = ys.min(), ys.max()
    h = y1 - y0 + 1
    top = ys < y0 + h * 0.2
    bot = ys > y0 + h * 0.8
    if not top.any() or not bot.any():
        return 1.0
    tw = xs[top].max() - xs[top].min()
    bw = xs[bot].max() - xs[bot].min()
    return tw / max(bw, 1)


def barrel_on_left(mask: np.ndarray) -> bool:
    ys, xs = np.where(mask)
    cx = xs.mean()
    return (xs < cx).sum() > (xs >= cx).sum()


def pick_source() -> tuple[Path, np.ndarray]:
    for path in SOURCE_CANDIDATES:
        if path.exists() and path.stat().st_size > 100:
            raw = load_rgb(path)
            h, w = raw.shape[:2]
            scale = UPSCALE_LONG / max(h, w)
            if scale > 1.01:
                raw = np.array(
                    Image.fromarray(raw).resize(
                        (int(w * scale), int(h * scale)), Image.Resampling.LANCZOS
                    )
                )
            return path, raw
    raise FileNotFoundError("no LADA source found")


def extract_padded(raw: np.ndarray, pad_frac: float = 0.35) -> np.ndarray:
    mask = content_mask(raw)
    x0, y0, x1, y1 = content_bbox(mask)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    pad = int(max(bw, bh) * pad_frac)
    canvas = np.full((bh + 2 * pad, bw + 2 * pad, 3), 255, dtype=np.uint8)
    crop = clean_on_white(raw, mask)[y0 : y1 + 1, x0 : x1 + 1]
    canvas[pad : pad + bh, pad : pad + bw] = crop
    return canvas


def perspective_unpitch_bbox(arr: np.ndarray, strength: float) -> tuple[np.ndarray, dict]:
    """
    Bbox-corner perspective warp.
    Push top edge up/back, compress top width vs bottom, expand bottom, nudge hub upright.
    """
    h, w = arr.shape[:2]
    mask = content_mask(arr)
    x0, y0, x1, y1 = content_bbox(mask)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    cx = (x0 + x1) / 2.0

    src = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])

    top_lift = bh * 0.20 * strength
    top_compress = 1.0 - 0.26 * strength
    bot_expand = 1.0 + 0.12 * strength
    hub_nudge = bh * 0.06 * strength

    half_top = bw / 2.0 * top_compress
    half_bot = bw / 2.0 * bot_expand
    bot_drop = bh * 0.06 * strength

    dst = np.float32(
        [
            [cx - half_top, y0 - top_lift],
            [cx + half_top, y0 - top_lift + hub_nudge],
            [cx + half_bot, y1 + bot_drop],
            [cx - half_bot, y1 + bot_drop * 0.5 - hub_nudge * 0.5],
        ]
    )

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(
        arr,
        M,
        (w, h),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
    meta = {
        "strength": strength,
        "top_lift_px": top_lift,
        "top_compress": top_compress,
        "bot_expand": bot_expand,
        "hub_nudge_px": hub_nudge,
        "bbox": (x0, y0, x1, y1),
    }
    return warped, meta


def ensure_orientation(arr: np.ndarray) -> np.ndarray:
    mask = content_mask(arr)
    if barrel_on_left(mask):
        return arr
    return cv2.flip(arr, 1)


def fit_canvas(arr: np.ndarray) -> Image.Image:
    mask = content_mask(arr)
    x0, y0, x1, y1 = content_bbox(mask)
    crop_arr = clean_on_white(arr, mask)
    crop = Image.fromarray(crop_arr).crop((max(0, x0 - 8), max(0, y0 - 8), x1 + 9, y1 + 9))
    tw, th = crop.size
    scale = min((TW * FILL) / tw, (TH * FILL) / th)
    nw, nh = max(1, int(tw * scale)), max(1, int(th * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    crop = ImageEnhance.Sharpness(crop).enhance(1.05)

    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    x = (TW - nw) // 2
    y = (TH - nh) // 2

    sh_layer = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    blob = Image.fromarray((content_mask(np.array(crop)).astype(np.uint8) * 200))
    shadow = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 48), (0, 0), blob)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    sh_layer.paste(shadow, (x + 6, y + 14), shadow)
    base = canvas.convert("RGBA")
    base = Image.alpha_composite(base, sh_layer)
    base.paste(crop.convert("RGBA"), (x, y), crop.convert("RGBA"))
    return base.convert("RGB")


def pick_strength(
    raw_padded: np.ndarray, ref_ratio: float, ref_tb: float
) -> tuple[float, np.ndarray, dict]:
    """Pick strongest viable warp that keeps face-right / barrel-left."""
    best_s, best_img, best_meta = 1.05, None, {}
    best_score = -1e9
    for s in (0.95, 1.05, 1.15):
        warped, meta = perspective_unpitch_bbox(raw_padded, s)
        warped = ensure_orientation(warped)
        mask = content_mask(warped)
        if not barrel_on_left(mask):
            continue
        ratio = face_vertical_ratio(fit_outer_ellipse(mask))
        tb = top_bottom_width_ratio(mask)
        # Prefer stronger unpitch up to 1.15; penalise overshoot past ref ratio
        score = s * 10.0 - abs(tb - ref_tb) * 1.5 - max(0.0, ratio - ref_ratio - 0.18) * 6.0
        if score > best_score:
            best_score = score
            best_s, best_img, best_meta = s, warped, meta
    if best_img is None:
        best_img, best_meta = perspective_unpitch_bbox(raw_padded, 1.05)
        best_img = ensure_orientation(best_img)
        best_s = 1.05
    best_meta["chosen_strength"] = best_s
    return best_s, best_img, best_meta


def save_outputs(canvas: Image.Image, thumb_qa: Image.Image) -> None:
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
    thumb_qa.save(TMP / "lada-strong-thumb.jpg", "JPEG", quality=85, optimize=True)


def make_contact_sheet(lada_thumb: Image.Image) -> None:
    black = Image.open(REF_PATH).copy()
    black.thumbnail((360, 480))
    lada = lada_thumb.copy()
    lada.thumbnail((360, 480))
    h = max(lada.height, black.height)
    pad = 12
    sheet = Image.new("RGB", (lada.width + black.width + pad * 3, h + pad * 2), (240, 240, 240))
    sheet.paste(lada, (pad, (h - lada.height) // 2 + pad))
    sheet.paste(black, (pad * 2 + lada.width, (h - black.height) // 2 + pad))
    sheet.save(TMP / "lada-vs-black.jpg", "JPEG", quality=90)


def main() -> None:
    ref = load_rgb(REF_PATH)
    ref_mask = content_mask(ref)
    ref_ratio = face_vertical_ratio(fit_outer_ellipse(ref_mask))
    ref_tb = top_bottom_width_ratio(ref_mask)

    src_path, raw = pick_source()
    padded = extract_padded(raw)
    src_ratio = face_vertical_ratio(fit_outer_ellipse(content_mask(padded)))
    print(f"source={src_path.name}  upscaled_long={UPSCALE_LONG}")
    print(f"ref ratio={ref_ratio:.4f} tb={ref_tb:.3f}  src ratio={src_ratio:.4f}")
    print(f"barrel left (raw): {barrel_on_left(content_mask(padded))}")

    strength, warped, meta = pick_strength(padded, ref_ratio, ref_tb)
    wmask = content_mask(warped)
    wratio = face_vertical_ratio(fit_outer_ellipse(wmask))
    wtb = top_bottom_width_ratio(wmask)
    print(f"warp strength={strength:.2f}  top_lift={meta.get('top_lift_px', 0):.1f}px")
    print(f"top_compress={meta.get('top_compress', 0):.3f}  bot_expand={meta.get('bot_expand', 0):.3f}")
    print(f"final ratio={wratio:.4f} tb={wtb:.3f}  barrel left={barrel_on_left(wmask)}")

    canvas = fit_canvas(warped)
    thimg = canvas.copy()
    thimg.thumbnail((360, 480))
    save_outputs(canvas, thimg)
    make_contact_sheet(thimg)
    print("saved public/dist/backend + .tmp-disk/lada-strong-thumb.jpg + lada-vs-black.jpg")
    print("option=A (strong bbox perspective unpitch)")


if __name__ == "__main__":
    main()
