#!/usr/bin/env python3
"""Process user-provided VENTI 1704 photo — fresh from asset, no reuse of public JPG."""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

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


def paste_mask(arr: np.ndarray) -> np.ndarray:
    """Wheel silhouette for alpha paste — light erode drops 1px frame hairlines only."""
    base = content_mask(arr).astype(np.uint8) * 255
    return cv2.erode(base, np.ones((3, 3), np.uint8), iterations=1) > 0


def content_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def barrel_on_left(mask: np.ndarray) -> bool:
    ys, xs = np.where(mask)
    cx = xs.mean()
    return (xs < cx).sum() > (xs >= cx).sum()


def local_mean(img: np.ndarray, ksize: int = 11) -> np.ndarray:
    gray = img.mean(axis=2).astype(np.float32)
    return cv2.GaussianBlur(gray, (ksize, ksize), 0)


def _hub_mask(wheel: np.ndarray) -> np.ndarray:
    ys, xs = np.where(wheel)
    cy, cx = int(ys.mean()), int(xs.mean())
    y0, y1 = ys.min(), ys.max()
    r = int((y1 - y0) * 0.17)
    yy, xx = np.ogrid[: wheel.shape[0], : wheel.shape[1]]
    return ((yy - cy) ** 2 + (xx - cx) ** 2) <= r * r


def strip_source_border_frame(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Remove embedded-photo L-frame and border lines from source before compositing."""
    h, w = img.shape[:2]
    out = img.copy()
    margin = max(35, int(min(h, w) * 0.09))
    total = 0

    for _ in range(4):
        neigh = local_mean(out)
        maxc = out.max(axis=2)
        mask = np.zeros((h, w), dtype=bool)

        edge = np.zeros((h, w), dtype=bool)
        edge[:margin, :] = True
        edge[h - margin :, :] = True
        edge[:, :margin] = True
        edge[:, w - margin :] = True
        mask |= edge & (maxc < 200) & (neigh > 208)

        # Horizontal frame runs in bottom/top margin bands.
        for y in range(h - margin, h):
            dark = (maxc[y, :] < 120) & (neigh[y, :] > 215)
            if dark.sum() > 8:
                mask[y, dark] = True
        for y in range(margin):
            dark = (maxc[y, :] < 120) & (neigh[y, :] > 215)
            if dark.sum() > 8:
                mask[y, dark] = True

        # Vertical frame runs in left/right margin bands.
        for x in range(w - margin, w):
            dark = (maxc[:, x] < 120) & (neigh[:, x] > 215)
            if dark.sum() > 8:
                mask[dark, x] = True
        for x in range(margin):
            dark = (maxc[:, x] < 120) & (neigh[:, x] > 215)
            if dark.sum() > 8:
                mask[dark, x] = True

        count = int(mask.sum())
        if not count:
            break
        out[mask] = (255, 255, 255)
        total += count

    return out, total


def gentle_diagonal_watermark_mask(img: np.ndarray, wheel: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    local = cv2.GaussianBlur(gray, (0, 0), 7)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)

    lifted = (gray - local) > 4
    grayish = (gray > 35) & (gray < 225) & (sat < 70)
    dark_base = local < 155

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    diag = mag > 14

    hub = _hub_mask(wheel)
    wm = wheel & ~hub & lifted & grayish & dark_base & diag
    wm = cv2.morphologyEx(wm.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), 1) > 0
    return wm


def _donor_from_flip(out: np.ndarray, wheel: np.ndarray, repair: np.ndarray) -> np.ndarray:
    if not repair.any():
        return out
    result = out.copy()
    flipped = cv2.flip(result, 1)
    ry, rx = np.where(repair)
    fx = (out.shape[1] - 1 - rx).astype(np.int32)
    donor_ok = wheel[ry, fx] & ~repair[ry, fx]
    result[ry[donor_ok], rx[donor_ok]] = flipped[ry[donor_ok], rx[donor_ok]]
    return result


def polish_dark_spokes(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Broad TELEA pass: any lifted gray streak on local-dark spoke surfaces."""
    wheel = content_mask(img)
    hub = _hub_mask(wheel)
    gray = img.mean(axis=2).astype(np.float32)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)
    local = cv2.GaussianBlur(gray, (0, 0), 11)
    wm = wheel & ~hub & (local < 120) & (sat < 80) & ((gray - local) > 2.5) & (gray < 200)
    count = int(wm.sum())
    if count < 50:
        return img, count
    mask = cv2.dilate(wm.astype(np.uint8) * 255, np.ones((2, 2), np.uint8), 1)
    out = cv2.inpaint(img, mask, 6, cv2.INPAINT_TELEA)
    return _donor_from_flip(out, wheel, wm), count


def remove_watermark(img: np.ndarray) -> tuple[np.ndarray, int]:
    """2–3 TELEA passes on faint brighter-than-local streaks over dark spokes."""
    wheel = content_mask(img)
    hub = _hub_mask(wheel)
    out = img.copy()
    total = 0
    for iteration, radius in enumerate((4, 6, 8, 10)):
        wm = gentle_diagonal_watermark_mask(out, wheel) & ~hub
        count = int(wm.sum())
        if count < 15 and iteration >= 2:
            break
        if count < 8:
            break
        mask = cv2.dilate(wm.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 1)
        out = cv2.inpaint(out, mask, radius, cv2.INPAINT_TELEA)
        out = _donor_from_flip(out, wheel, wm)
        total += count
    return out, total


def scrub_background(img: np.ndarray) -> np.ndarray:
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


def add_soft_shadow(canvas: Image.Image) -> Image.Image:
    arr = np.array(canvas)
    mask = content_mask(arr)
    if not mask.any():
        return canvas
    x0, y0, x1, y1 = content_bbox(mask)
    shadow = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    oval = Image.new("L", canvas.size, 0)
    cx, cy = (x0 + x1) // 2, y1 + 18
    rx, ry = int((x1 - x0) * 0.38), 16
    draw = ImageDraw.Draw(oval)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=90)
    oval = oval.filter(ImageFilter.GaussianBlur(12))
    shadow.paste((220, 220, 220), mask=oval)
    base = canvas.convert("RGBA")
    base.alpha_composite(shadow)
    return base.convert("RGB")


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
    y = (TH - nh) // 2
    # Paste wheel silhouette only — no source background / frame artifacts.
    crop_arr = np.array(crop)
    crop_mask = paste_mask(crop_arr)
    crop_rgba = Image.fromarray(crop_arr).convert("RGBA")
    alpha = Image.fromarray((crop_mask.astype(np.uint8) * 255), mode="L")
    crop_rgba.putalpha(alpha)
    canvas.paste(crop_rgba, (x, y), crop_rgba)
    return add_soft_shadow(canvas)


def post_canvas_watermark_pass(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Final TELEA pass on fitted canvas — spokes only, not bbox perimeter."""
    wheel = content_mask(img)
    x0, y0, x1, y1 = content_bbox(wheel)
    h, w = img.shape[:2]
    inset = np.zeros((h, w), dtype=bool)
    pad = 40
    inset[max(y0 + pad, 0) : min(y1 - pad, h - 1) + 1, max(x0 + pad, 0) : min(x1 - pad, w - 1) + 1] = True

    hub = _hub_mask(wheel)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    local = cv2.GaussianBlur(gray, (0, 0), 9)
    sat = hsv[:, :, 1].astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    out = img.copy()
    total = 0
    for radius in (3, 5, 7):
        wm = (
            wheel
            & inset
            & ~hub
            & (local < 135)
            & (sat < 75)
            & ((gray - local) > 3)
            & (gray < 215)
            & (mag > 8)
        )
        count = int(wm.sum())
        if count < 60:
            break
        mask = cv2.dilate(wm.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 1)
        out = cv2.inpaint(out, mask, radius, cv2.INPAINT_TELEA)
        out = _donor_from_flip(out, wheel, wm)
        gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32)
        local = cv2.GaussianBlur(gray, (0, 0), 9)
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1].astype(np.float32)
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        total += count
    return out, total


def trim_bbox_artifact_bands(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Remove scaled embedded-photo L-frame bars at wheel bbox bottom/right."""
    out = img.copy()
    maxc = out.max(axis=2)
    gray = out.mean(axis=2)
    wheel = content_mask(out)
    x0, y0, x1, y1 = content_bbox(wheel)
    count = 0
    width = x1 - x0 + 1

    # Find last "natural" wheel row — before sudden full-width pure-black bar.
    last_good = y0
    for y in range(y0, y1 + 1):
        dark = int((maxc[y, x0 : x1 + 1] < 120).sum())
        if dark < width * 0.35:
            last_good = y

    if last_good < y1 - 8:
        wipe = out[last_good + 1 : y1 + 1, x0 : x1 + 1]
        count += int((wipe.max(axis=2) < 200).sum())
        out[last_good + 1 : y1 + 1, x0 : x1 + 1] = (255, 255, 255)

    # Right edge: cols beyond last good wheel column in bottom third.
    y_mid = y0 + (last_good - y0) * 2 // 3
    for x in range(x1, max(x0, x1 - 80), -1):
        col = maxc[y_mid : last_good + 1, x]
        if col.size and (col < 20).sum() > col.size * 0.5:
            band = out[y0 : y1 + 1, x : x1 + 1]
            count += int((band.max(axis=2) < 200).sum())
            out[y0 : y1 + 1, x : x1 + 1] = (255, 255, 255)
            break

    # Canvas-edge dark lines outside padded bbox (L-frame on white).
    h, w = out.shape[:2]
    pad = 20
    px0, py0, px1, py1 = max(0, x0 - pad), max(0, y0 - pad), min(w - 1, x1 + pad), min(h - 1, y1 + pad)
    neigh = local_mean(out)
    edge = np.zeros((h, w), dtype=bool)
    edge[:, px1 + 1 :] = True
    edge[last_good + 1 :, :] = True
    wipe = edge & (maxc < 80) & (neigh > 230)
    wipe |= edge & (gray < 245) & (maxc < 120)
    count += int(wipe.sum())
    out[wipe] = (255, 255, 255)

    return out, count


def strip_margin_outside_core(img: np.ndarray) -> tuple[np.ndarray, int]:
    """In outer ~10% margin, keep only eroded wheel core — drops attached L-frame."""
    h, w = img.shape[:2]
    wheel = content_mask(img)
    core = cv2.erode(wheel.astype(np.uint8) * 255, np.ones((11, 11), np.uint8), 2) > 0
    m = max(30, int(min(h, w) * 0.1))
    margin = np.zeros((h, w), dtype=bool)
    margin[:m, :] = True
    margin[h - m :, :] = True
    margin[:, :m] = True
    margin[:, w - m :] = True
    wipe = margin & wheel & ~core
    out = img.copy()
    count = int(wipe.sum())
    if count:
        out[wipe] = (255, 255, 255)
    return out, count


def clean_output_margins(img: np.ndarray) -> tuple[np.ndarray, int]:
    """Pure white margins; strip any frame/crop lines outside padded wheel bbox."""
    h, w = img.shape[:2]
    mask = content_mask(img)
    x0, y0, x1, y1 = content_bbox(mask)
    px0, py0, px1, py1 = (
        max(0, x0 - 20),
        max(0, y0 - 20),
        min(w - 1, x1 + 20),
        min(h - 1, y1 + 20),
    )
    out = img.copy()
    outside = np.ones((h, w), dtype=bool)
    outside[py0 : py1 + 1, px0 : px1 + 1] = False
    count = int(outside.sum())
    out[outside] = (255, 255, 255)

    neigh = local_mean(out)
    maxc = out.max(axis=2)
    ring = np.zeros((h, w), dtype=bool)
    ring[py0 : py1 + 1, px0 : px1 + 1] = True
    ring[y0 : y1 + 1, x0 : x1 + 1] = False
    line_px = ring & (maxc < 180) & (neigh > 228)
    count += int(line_px.sum())
    out[line_px] = (255, 255, 255)

    # Edge strips: near-black on white anywhere in canvas margins.
    for _ in range(3):
        neigh = local_mean(out)
        maxc = out.max(axis=2)
        edge = np.zeros((h, w), dtype=bool)
        edge[:, :max(1, px0)] = True
        edge[:, min(w, px1 + 1) :] = True
        edge[min(h, py1 + 1) :, :] = True
        edge[:max(1, py0), :] = True
        wipe = edge & (maxc < 180) & (neigh > 228)
        wipe |= edge & (maxc < 50)
        if not wipe.any():
            break
        count += int(wipe.sum())
        out[wipe] = (255, 255, 255)

    return out, count


def _runs(indices: np.ndarray, gap: int = 2) -> list[tuple[int, int]]:
    if len(indices) == 0:
        return []
    breaks = np.where(np.diff(indices) > gap)[0]
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [len(indices) - 1]))
    return [(int(indices[s]), int(indices[e])) for s, e in zip(starts, ends)]


def _edge_line_runs(img: np.ndarray, margin: int = 40) -> dict[str, list[tuple[int, int]]]:
    """Detect continuous dark line runs along bottom/right canvas edges."""
    h, w = img.shape[:2]
    maxc = img.max(axis=2)
    dark = maxc < 80
    neigh = local_mean(img)
    on_white = neigh > 235

    out: dict[str, list[tuple[int, int]]] = {}
    # Right edge strip
    right = dark[:, w - margin :] & on_white[:, w - margin :]
    for x in range(margin):
        ys = np.where(right[:, x])[0]
        for a, b in _runs(ys):
            if b - a + 1 >= 12:
                out.setdefault("right", []).append((a, b))
    # Bottom edge strip
    bottom = dark[h - margin :, :] & on_white[h - margin :, :]
    for y in range(margin):
        xs = np.where(bottom[y, :])[0]
        for a, b in _runs(xs):
            if b - a + 1 >= 12:
                out.setdefault("bottom", []).append((a, b))
    return out


def qa_canvas(img: np.ndarray) -> dict:
    h, w = img.shape[:2]
    maxc = img.max(axis=2)
    margin = 40
    mask = content_mask(img)
    x0, y0, x1, y1 = content_bbox(mask)
    issues = []

    # Outer 40px margin: no pixels with max(RGB) < 60
    outer = np.zeros((h, w), dtype=bool)
    outer[:margin, :] = True
    outer[h - margin :, :] = True
    outer[:, :margin] = True
    outer[:, w - margin :] = True
    nb60 = int((outer & (maxc < 60)).sum())
    if nb60:
        issues.append(f"outer40_max_lt60={nb60}")

    # Continuous dark line runs on bottom/right canvas edges
    line_runs = _edge_line_runs(img, margin)
    for edge, runs in line_runs.items():
        if runs:
            issues.append(f"{edge}_dark_runs={len(runs)}")

    # Bbox bottom band: no full-width pure-black bar (scaled L-frame)
    width = x1 - x0 + 1
    bbox_bottom_pure = 0
    for y in range(max(y0, y1 - 25), y1 + 1):
        pure = int((maxc[y, x0 : x1 + 1] < 15).sum())
        if pure > width * 0.15:
            bbox_bottom_pure += pure
    if bbox_bottom_pure:
        issues.append(f"bbox_bottom_pure_black={bbox_bottom_pure}")

    return {
        "clean": len(issues) == 0,
        "issues": issues,
        "size": (w, h),
        "barrel_on_left": barrel_on_left(mask),
        "outer40_max_lt60": nb60,
        "edge_line_runs": line_runs,
        "bbox_bottom_pure_black": bbox_bottom_pure,
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
    canvas.save(TMP / "venti1704-clean2.jpg", "JPEG", quality=90, optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Source not found: {SOURCE}")

    raw = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"source={SOURCE.name} size={raw.shape[1]}x{raw.shape[0]}")

    mask = content_mask(raw)
    print(f"barrel_on_left={barrel_on_left(mask)} (False=face-right, no flip)")

    img = raw
    if not barrel_on_left(mask):  # barrel-right / face-left → flip to face-right
        img = cv2.flip(img, 1)
        mask = content_mask(img)
        print(f"flipped -> barrel_on_left={barrel_on_left(mask)}")

    img, frame_px = strip_source_border_frame(img)
    print(f"source_frame_pixels_whitened={frame_px}")

    img, margin_core_px = strip_margin_outside_core(img)
    print(f"source_margin_outside_core_whitened={margin_core_px}")

    img, wm_px = remove_watermark(img)
    print(f"watermark_pixels_inpainted={wm_px}")

    img, polish_px = polish_dark_spokes(img)
    print(f"dark_spoke_polish_pixels={polish_px}")

    img = scrub_background(img)
    canvas_arr = np.array(fit_canvas(img))
    canvas_arr, post_wm = post_canvas_watermark_pass(canvas_arr)
    print(f"post_canvas_watermark_pixels={post_wm}")
    canvas_arr, artifact_px = trim_bbox_artifact_bands(canvas_arr)
    print(f"bbox_artifact_pixels_whitened={artifact_px}")
    canvas_arr, margin_px = clean_output_margins(canvas_arr)
    print(f"margin_pixels_whitened={margin_px}")

    qa = qa_canvas(canvas_arr)
    print(f"QA: {qa}")
    if not qa["clean"]:
        print(f"WARNING: QA issues remain: {qa['issues']}")

    canvas = Image.fromarray(canvas_arr)
    save_outputs(canvas)

    full = PUBLIC / f"{STEM}.jpg"
    thumb = PUBLIC / f"{STEM}-thumb.jpg"
    print(f"full={full.stat().st_size} bytes {Image.open(full).size}")
    print(f"thumb={thumb.stat().st_size} bytes {Image.open(thumb).size}")
    print("saved public/dist/backend + .tmp-disk/venti1704-clean2.jpg")


if __name__ == "__main__":
    main()
