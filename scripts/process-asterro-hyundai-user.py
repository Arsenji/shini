#!/usr/bin/env python3
"""Install Asterro Hyundai — remove tiled «колеса даром» watermarks, face-right."""

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
STEM = "asterro-hyundai-78-gruzovoy-nocolor"
SOURCE = Path(
    "/Users/arsenijberdnikov/.cursor/projects/Users-arsenijberdnikov-Documents/assets/"
    "image-817e281b-324f-4ef2-bab6-610162643a6d.png"
)
TW, TH = 900, 1200
FILL = 0.84
MAX_SIDE = int(FILL * min(TW, TH))


def content_mask(arr: np.ndarray) -> np.ndarray:
    gray = arr.mean(axis=2) if arr.ndim == 3 else arr
    content = (gray < 248).astype(np.uint8) * 255
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


def rim_edge_mask(gray: np.ndarray, wheel: np.ndarray) -> np.ndarray:
    """Protect silhouette / hole boundaries only (not interior metal highlights)."""
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    near_bg = cv2.dilate((~wheel).astype(np.uint8), np.ones((5, 5), np.uint8), 2) > 0
    near_white = cv2.dilate((gray > 245).astype(np.uint8), np.ones((3, 3), np.uint8), 1) > 0
    return (mag > 50) & (near_bg | near_white)


def find_logo_hits(exc_u8: np.ndarray) -> list[tuple[int, int, float, int, int]]:
    h, w = exc_u8.shape
    # Face logos (2-line «колеса даром» + icon); avoid highlight-heavy sidewall crop
    tmpl_boxes = [(424, 271, 95, 40), (100, 288, 70, 28), (219, 73, 100, 36)]
    hits: list[tuple[int, int, float, int, int]] = []
    for x, y, tw, th in tmpl_boxes:
        if y + th > h or x + tw > w:
            continue
        te = exc_u8[y : y + th, x : x + tw]
        for scale in (0.88, 1.0, 1.12):
            tw2, th2 = max(20, int(tw * scale)), max(12, int(th * scale))
            te2 = cv2.resize(te, (tw2, th2), interpolation=cv2.INTER_AREA)
            res = cv2.matchTemplate(exc_u8, te2, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(res >= 0.30)
            pts = sorted(
                zip(xs.tolist(), ys.tolist(), res[ys, xs].tolist()),
                key=lambda t: -t[2],
            )
            local: list[tuple[int, int, float]] = []
            for px, py, s in pts:
                if any(
                    abs(px - qx) < tw2 * 0.42 and abs(py - qy) < th2 * 0.42
                    for qx, qy, _ in local
                ):
                    continue
                local.append((px, py, float(s)))
                hits.append((px, py, float(s), tw2, th2))
    hits.sort(key=lambda t: -t[2])
    final: list[tuple[int, int, float, int, int]] = []
    for px, py, s, tw, th in hits:
        if s < 0.30:
            continue
        if any(abs(px - qx) < 34 and abs(py - qy) < 20 for qx, qy, _, _, _ in final):
            continue
        final.append((px, py, s, tw, th))
    return final


def remove_tiled_watermarks(img: np.ndarray) -> tuple[np.ndarray, int]:
    """
    Multi-pass tiled-logo removal:
    1) template-match 2-line logos
    2) simultaneous median-donor fill (avoids TELEA reintroducing neighbors' logos)
    3) residual excess passes with carefully lowered thresholds
    Rim/hole edges protected.
    """
    h, w = img.shape[:2]
    out = img.copy()
    wheel = content_mask(out)
    gray = out.mean(axis=2).astype(np.float32)
    rim = rim_edge_mask(gray, wheel)

    exc = gray - cv2.GaussianBlur(gray, (0, 0), 2.5)
    exc_u8 = np.clip(exc * 10 + 128, 0, 255).astype(np.uint8)
    hits = find_logo_hits(exc_u8)

    mask = np.zeros((h, w), np.uint8)
    for px, py, _s, tw, th in hits:
        x0, y0 = max(0, px - 4), max(0, py - 3)
        x1, y1 = min(w, px + tw + 4), min(h, py + th + 3)
        cv2.ellipse(
            mask,
            ((x0 + x1) // 2, (y0 + y1) // 2),
            (max(1, (x1 - x0) // 2), max(1, (y1 - y0) // 2)),
            0,
            0,
            360,
            255,
            -1,
        )

    mask[~wheel] = 0
    mask[rim] = 0

    if int((mask > 0).sum()) < 80:
        return out, 0

    # Simultaneous median donors — all logos at once so neighbors are clean
    for k in (11, 15, 19):
        med = cv2.medianBlur(out if k > 11 else img, k)
        m = cv2.GaussianBlur(mask, (0, 0), 1.8).astype(np.float32) / 255.0
        core = cv2.erode(mask, np.ones((2, 2), np.uint8), 1)
        out = np.clip(
            out.astype(np.float32) * (1 - m[:, :, None])
            + med.astype(np.float32) * m[:, :, None],
            0,
            255,
        ).astype(np.uint8)
        out[core > 0] = med[core > 0]

    border = cv2.dilate(mask, np.ones((4, 4), np.uint8), 1)
    border = cv2.bitwise_and(
        border, cv2.bitwise_not(cv2.erode(mask, np.ones((4, 4), np.uint8), 1))
    )
    border[rim] = 0
    if border.any():
        out = cv2.inpaint(out, border, 2, cv2.INPAINT_TELEA)

    total = int((mask > 0).sum())
    near = cv2.dilate(mask, np.ones((25, 25), np.uint8), 1)

    # Residual passes — lower excess threshold carefully near known logos
    for thr in (2.8, 2.2, 1.7, 1.3):
        g = out.mean(axis=2).astype(np.float32)
        ex = g - cv2.GaussianBlur(g, (0, 0), 2.5)
        wheel2 = content_mask(out)
        rim2 = rim_edge_mask(g, wheel2)
        cand = (
            wheel2
            & (near > 0)
            & ~rim2
            & (ex > thr)
            & (g > 115)
            & (g < 232)
        )
        mu = cand.astype(np.uint8) * 255
        mu = cv2.morphologyEx(mu, cv2.MORPH_CLOSE, np.ones((2, 7), np.uint8), 2)
        n, lab, st, _ = cv2.connectedComponentsWithStats(mu, 8)
        keep = np.zeros((h, w), np.uint8)
        for i in range(1, n):
            area = int(st[i, cv2.CC_STAT_AREA])
            bw = int(st[i, cv2.CC_STAT_WIDTH])
            bh = int(st[i, cv2.CC_STAT_HEIGHT])
            if 25 <= area <= 3000 and 7 <= bh <= 38 and bw >= 12:
                keep[lab == i] = 255
        keep = cv2.dilate(keep, np.ones((2, 2), np.uint8), 1)
        keep[rim2] = 0
        px = int((keep > 0).sum())
        if px < 40:
            continue
        med = cv2.medianBlur(out, 13)
        m = cv2.GaussianBlur(keep, (0, 0), 1.2).astype(np.float32) / 255.0
        out = np.clip(
            out.astype(np.float32) * (1 - m[:, :, None])
            + med.astype(np.float32) * m[:, :, None],
            0,
            255,
        ).astype(np.uint8)
        total += px
        near = cv2.bitwise_or(near, cv2.dilate(keep, np.ones((15, 15), np.uint8), 1))

    return out, total


def fit_canvas(arr: np.ndarray) -> Image.Image:
    mask = content_mask(arr)
    ys, xs = np.where(mask)
    pad = 10
    x0, x1 = max(0, int(xs.min()) - pad), min(arr.shape[1], int(xs.max()) + pad + 1)
    y0, y1 = max(0, int(ys.min()) - pad), min(arr.shape[0], int(ys.max()) + pad + 1)
    crop = arr[y0:y1, x0:x1].copy()
    cmask = content_mask(crop)
    crop[~cmask] = (255, 255, 255)
    ch, cw = crop.shape[:2]
    scale = MAX_SIDE / max(cw, ch)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = Image.fromarray(crop).resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    canvas.paste(resized, ((TW - nw) // 2, (TH - nh) // 2))
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
    canvas.save(TMP / "asterro-hyundai-new.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")
    img = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={img.shape[1]}x{img.shape[0]}")

    mask0 = content_mask(img)
    bl = barrel_on_left(mask0)
    print(f"barrel_on_left_heuristic={bl}")
    print("keeping source orientation (face-right)")

    cleaned, wm_px = remove_tiled_watermarks(img)
    print(f"watermark_pixels_inpainted={wm_px}")

    canvas = fit_canvas(cleaned)
    arr, edge_px = clean_canvas_edge_artifacts(np.array(canvas))
    print(f"canvas_edge_artifacts_whitened={edge_px}")
    save_outputs(Image.fromarray(arr))
    full = PUBLIC / f"{STEM}.jpg"
    print(f"full={full.stat().st_size}b {Image.open(full).size}")
    print("saved + .tmp-disk/asterro-hyundai-new.jpg")


if __name__ == "__main__":
    main()
