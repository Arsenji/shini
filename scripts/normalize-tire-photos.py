#!/usr/bin/env python3
"""Replace catalog reference photos with full, same-direction, dewatermarked shots."""

from __future__ import annotations

import re
import subprocess
import urllib.parse
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "src/data/shop/products.ts"
LOG = ROOT / "reference-photos/download-log.tsv"
OUT = ROOT / "public/tires"
UA = "Mozilla/5.0"


def slug(value: str) -> str:
    value = value.lower().replace("ё", "е").replace("\\", " ").replace("/", "-")
    return re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.I).strip("-")


def products() -> list[tuple[str, str, str]]:
    text = PRODUCTS.read_text(encoding="utf-8")
    rows = []
    for match in re.finditer(
        r"\{\s*id:\s*'([^']+)',\s*brand:\s*'([^']*)',\s*model:\s*'([^']*)',(.*?)(?=\n  \},|\n\];)",
        text,
        re.S,
    ):
        images = re.findall(r"image:\s*'([^']+)'", match.group(4))
        if images and images[0].endswith(".jpg"):
            rows.append((match.group(1), match.group(2), match.group(3)))
    return rows


def log_urls() -> dict[tuple[str, str], list[str]]:
    found: dict[tuple[str, str], list[str]] = {}
    for line in LOG.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) < 5 or parts[0] not in {"ok", "retry"}:
            continue
        brand, model, url = parts[1], parts[2], parts[4]
        if not url.startswith("http"):
            continue
        found.setdefault((slug(brand), slug(model)), []).append(url)
    return found


def studio_candidates(url: str) -> list[str]:
    if "mosautoshina.ru/i/tyre/" not in url:
        return []
    if any(part in url for part in ("/anfas/", "/protector/", "/wb/")):
        return []
    name = url.split("?", 1)[0].rsplit("/", 1)[-1]
    name = re.sub(r"-(max|500@2x|500|400)\.(jpg|png|webp)$", "", name, flags=re.I)
    if not name:
        return []
    return [
        f"https://mosautoshina.ru/i/tyre/{name}-500@2x.jpg",
        f"https://mosautoshina.ru/i/tyre/{name}-500.jpg",
    ]


def curl(url: str, dest: Path) -> bool:
    try:
        subprocess.check_call(
            ["curl", "-fsL", "--max-time", "20", "-A", UA, "-o", str(dest), url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return dest.exists() and dest.stat().st_size > 8000


def near_white(rgb: tuple[int, int, int]) -> bool:
    return rgb[0] > 246 and rgb[1] > 246 and rgb[2] > 246


def content_box(im: Image.Image) -> tuple[int, int, int, int] | None:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    minx, miny, maxx, maxy = w, h, 0, 0
    found = False
    step = 2
    for y in range(0, h, step):
        for x in range(0, w, step):
            if not near_white(px[x, y]):
                found = True
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if not found:
        return None
    return max(0, minx - step), max(0, miny - step), min(w - 1, maxx + step), min(h - 1, maxy + step)


def heavily_cropped(im: Image.Image) -> bool:
    """True when rubber is cut off by the frame, not merely close to the edge."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()

    def dark(x: int, y: int) -> bool:
        r, g, b = px[x, y]
        return r < 90 and g < 90 and b < 90

    edges = (
        sum(1 for y in range(h) if dark(1, y)) / h,
        sum(1 for y in range(h) if dark(w - 2, y)) / h,
        sum(1 for x in range(w) if dark(x, 1)) / w,
        sum(1 for x in range(w) if dark(x, h - 2)) / w,
    )
    return max(edges) > 0.22


def hyphenate_codes(value: str) -> str:
    return re.sub(r"([a-z])(\d)", r"\1-\2", value)


ALIASES = {
    "kama-breeze-132": ["kama-breeze"],
    "kumho-kc-53": ["kumho-portran-kc53", "kumho-kc53"],
    "mirage-mr200": ["mirage-mr-200"],
    "sava-intenza": ["sava-intensa", "sava-intenza"],
    "yokohama-ae51": ["yokohama-bluearth-ae51"],
    "yokohama-es32": ["yokohama-bluearth-es32"],
    "yokohama-bluearth-es-es32": ["yokohama-bluearth-es32"],
    "yokohama-bluearth-es-es32-88h": ["yokohama-bluearth-es32"],
    "torero-mp47": ["torero-mp-47", "matador-mp-47"],
    "torero-mp82": ["torero-mp-82"],
    "torero-mp30-winter": ["torero-mp-30"],
    "pirelli-inturato-p7": ["pirelli-cinturato-p7"],
    "pirelli-p1-cinturato-verde": ["pirelli-cinturato-p1-verde"],
    "michelin-enerdgy-xm2": ["michelin-energy-xm2"],
    "michelin-energy-xm2-91v-1sht": ["michelin-energy-xm2"],
    "roadstone-hp02": ["roadstone-eurovis-hp02"],
    "kumho-hs-52": ["kumho-hs52"],
    "kumho-hs51-m": ["kumho-hs51"],
    "kumho-kc-11-winter": ["kumho-kc11"],
    "nokian-nordman-sx2": ["nokian-nordman-sx2", "ikon-nordman-sx2"],
    "linglong-lmc6": ["linglong-lmc6"],
    "ling-long-lmc6": ["linglong-lmc6"],
    "maxxis-me3-mecotra": ["maxxis-me3"],
    "kama-242": ["kama-242"],
    "kama-505-winter": ["kama-505"],
    "kama-alga-winter": ["kama-alga"],
    "kama-nk-434": ["kama-flame"],
    "delinte-195r14c-dv2": ["delinte-dv2"],
    "contyre-megapolis3": ["contyre-megapolis-3"],
    "landsail-clv2": ["landsail-clv2"],
    "nexen-nfera-ru5": ["roadstone-nfera-ru5", "nexen-nfera-ru5"],
    "roadstone-nfera-ru5": ["roadstone-nfera-ru5"],
}


def rim_on_left(im: Image.Image) -> bool:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    box = content_box(rgb)
    if not box:
        return False
    x0, y0, x1, y1 = box
    mid = (x0 + x1) / 2
    left = right = 0
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            r, g, b = px[x, y]
            if near_white((r, g, b)):
                continue
            # metallic rim: bright and not a pure rubber highlight only on one groove
            if r > 145 and g > 145 and b > 140 and max(r, g, b) - min(r, g, b) < 40:
                if x < mid:
                    left += 1
                else:
                    right += 1
    # Studio downloads are already tread-left / rim-right. Bright tread grooves
    # fooled the old detector into flipping correct photos.
    return False


def strip_orange_logo(im: Image.Image) -> Image.Image:
    rgb = im.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    orange = []
    for y in range(int(h * 0.7), h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 190 and 90 < g < 200 and b < 90 and r > g + 50:
                orange.append((x, y))
    if len(orange) < 60:
        return rgb
    for x, y in orange:
        px[x, y] = (255, 255, 255)
    # cover the text band just around the orange blob with white if it sits on background
    ys = [p[1] for p in orange]
    xs = [p[0] for p in orange]
    y0, y1 = max(0, min(ys) - 6), min(h - 1, max(ys) + 8)
    x0, x1 = max(0, min(xs) - 10), min(w - 1, max(xs) + 10)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            r, g, b = px[x, y]
            if r > 230 and g > 180 and b < 120:
                px[x, y] = (255, 255, 255)
    return rgb


def soften_tiled_watermark(im: Image.Image) -> Image.Image:
    """Pull light watermark text toward nearby rubber, skipping the metal rim."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    src = rgb.copy()
    px = rgb.load()
    sp = src.load()
    radius = 4
    for y in range(radius, h - radius, 2):
        for x in range(radius, w - radius, 2):
            r, g, b = sp[x, y]
            if near_white((r, g, b)) or max(r, g, b) - min(r, g, b) > 26:
                continue
            if r < 80 or r > 200:
                continue
            dark = 255
            for dy in (-radius, radius):
                for dx in (-radius, radius):
                    rr, gg, bb = sp[x + dx, y + dy]
                    lum = (rr + gg + bb) / 3
                    if lum < dark and not near_white((rr, gg, bb)):
                        dark = lum
            lum = (r + g + b) / 3
            if dark < 170 and lum > dark + 16 and lum < dark + 65:
                target = int(dark + (lum - dark) * 0.2)
                px[x, y] = (target, target, target)
                if x + 1 < w:
                    px[x + 1, y] = (target, target, target)
                if y + 1 < h:
                    px[x, y + 1] = (target, target, target)
    return rgb


def pad_full_tire(im: Image.Image) -> Image.Image:
    rgb = im.convert("RGB")
    box = content_box(rgb)
    if not box:
        return rgb
    x0, y0, x1, y1 = box
    tire = rgb.crop((x0, y0, x1 + 1, y1 + 1))
    tw, th = tire.size
    pad = max(18, int(max(tw, th) * 0.04))
    canvas = Image.new("RGB", (tw + pad * 2, th + pad * 2), (255, 255, 255))
    canvas.paste(tire, (pad, pad))
    return canvas


def prepare(im: Image.Image) -> Image.Image:
    im = strip_orange_logo(im)
    im = soften_tiled_watermark(im)
    if rim_on_left(im):
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return pad_full_tire(im)


def save_pair(im: Image.Image, product_id: str) -> None:
    full = OUT / f"{product_id}.jpg"
    thumb = OUT / f"{product_id}-thumb.jpg"
    fitted = im.copy()
    fitted.thumbnail((900, 1200), Image.Resampling.LANCZOS)
    fitted.save(full, "JPEG", quality=84, optimize=True)
    preview = fitted.copy()
    preview.thumbnail((360, 480), Image.Resampling.LANCZOS)
    preview.save(thumb, "JPEG", quality=78, optimize=True)


def main() -> None:
    urls = log_urls()
    rows = products()
    ok = fail = flipped = 0
    cache: dict[str, Path] = {}
    tmp = Path("/tmp/tire-normalize")
    tmp.mkdir(exist_ok=True)

    for index, (product_id, brand, model) in enumerate(rows, 1):
        candidates: list[str] = []
        for url in urls.get((slug(brand), slug(model)), []):
            candidates.extend(studio_candidates(url))
        brand_slug = slug(brand)
        model_slug = slug(model)
        compact = model_slug.replace("-", "")
        names = {
            f"{brand_slug}-{model_slug}",
            f"{brand_slug}-{compact}",
            hyphenate_codes(product_id),
            product_id,
        }
        names.update(ALIASES.get(product_id, []))
        for name in names:
            candidates.append(f"https://mosautoshina.ru/i/tyre/{name}-500@2x.jpg")
            candidates.append(f"https://mosautoshina.ru/i/tyre/{name}-500.jpg")

        seen = []
        for url in candidates:
            if url not in seen:
                seen.append(url)

        chosen = None
        for url in seen:
            dest = tmp / (re.sub(r"[^a-z0-9]+", "-", url)[-80:] + ".jpg")
            if url not in cache:
                if not curl(url, dest):
                    continue
                try:
                    probe = Image.open(dest)
                    probe.verify()
                except Exception:
                    continue
                cache[url] = dest
            probe = Image.open(cache[url])
            if heavily_cropped(probe):
                continue
            chosen = cache[url]
            break

        if chosen is None:
            fail += 1
            print(f"[{index}/{len(rows)}] KEEP {product_id}", flush=True)
            continue

        image = Image.open(chosen).convert("RGB")
        before = image
        if rim_on_left(image):
            flipped += 1
        image = prepare(image)
        save_pair(image, product_id)
        ok += 1
        print(f"[{index}/{len(rows)}] OK {product_id}", flush=True)

    print(f"DONE ok={ok} keep={fail} flipped={flipped}", flush=True)


if __name__ == "__main__":
    main()
