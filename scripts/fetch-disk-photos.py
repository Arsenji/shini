#!/usr/bin/env python3
"""Fetch wheel/disk catalog photos and wire them into products.ts."""

from __future__ import annotations

import re
import subprocess
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageEnhance
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "src/data/shop/products.ts"
PUBLIC = ROOT / "public/wheels"
DIST = ROOT / "dist/wheels"
BACKEND = ROOT / "backend/static/wheels"
TMP = ROOT / ".tmp-disk"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TW, TH, FILL = 900, 1200, 0.84

BRAND_SLUGS = {
    "x-trike": ["xtrike", "x-trike"],
    "tech line": ["techline", "tech-line"],
    "wheels up": ["wheels-up", "wheelsup"],
    "cross street": ["cross-street", "crossstreet"],
    "кик": ["kik", "k-k"],
    "киклинкс": ["kiklinks"],
    "скад": ["skad"],
    "тзск": ["tzsk"],
    "чкпз": ["chkpz"],
    "штампованный": ["stamp", "steel"],
    "грузовой": ["truck", "steel"],
    "ifree": ["ifree"],
    "neo": ["neo"],
    "venti": ["venti"],
    "rst": ["rst"],
    "yamato": ["yamato"],
    "megami": ["megami"],
    "replikey": ["replikey"],
    "accuride": ["accuride"],
    "asterro": ["asterro"],
    "sunrise": ["sunrise"],
    "trebl": ["trebl"],
    "nitro": ["nitro"],
    "n2o": ["n2o"],
    "n20": ["n20"],
    "pdw": ["pdw"],
    "remain": ["remain"],
    "lizardo": ["lizardo"],
    "yz": ["yz"],
}

COLOR_SLUGS = {
    "чёрный": ["bk", "black", "chernyy"],
    "черный": ["bk", "black"],
    "чёрный алмаз": ["bk-fp", "bk_fp", "black-diamond"],
    "черный алмаз": ["bk-fp", "bk_fp"],
    "алмаз чёрный": ["bk-fp", "bk_fp"],
    "алмаз черный": ["bk-fp"],
    "алмаз": ["almaz", "diamond", "hsb-fp"],
    "серебристый": ["hs", "silver", "serebristyy"],
    "гиперсеребро": ["hsb", "hs", "hypersilver"],
    "бронза": ["bronze", "br"],
    "сильвер": ["silver", "hs"],
    "silver classic": ["silver", "hs"],
    "new diamond": ["new-diamond", "nd", "diamond"],
    "new black": ["new-black", "nb", "bk"],
    "хай вэй": ["hay-vey", "hiway"],
    "блэк джек": ["blek-dzhek", "blackjack", "bk"],
    "чёрный бархат": ["chernyy-barhat", "bk"],
}


def slug(value: str) -> str:
    value = value.lower().replace("ё", "е").replace("\\", " ")
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.I)
    return value.strip("-")[:80] or "model"


def latin_model(model: str) -> str:
    model = model.lower().replace("ё", "е").replace("х-", "x-").replace("х", "x")
    model = re.sub(r"\(.*?\)", " ", model)
    model = re.sub(r"[^a-z0-9]+", "-", model)
    return model.strip("-")


def parse_disks(text: str) -> list[dict]:
    disks = []
    for block in re.split(r"\n  \{\n", text):
        if "category: 'disk'" not in block:
            continue

        def g(pat: str) -> str:
            m = re.search(pat, block)
            return m.group(1) if m else ""

        disks.append(
            {
                "id": g(r"id: '([^']+)'"),
                "brand": g(r"brand: '([^']+)'"),
                "model": g(r"model: '([^']+)'"),
                "badge": g(r"badge: '([^']+)'"),
                "color": g(r"color: '([^']+)'"),
            }
        )
    return [d for d in disks if d["id"]]


def curl_bytes(url: str) -> bytes | None:
    try:
        return subprocess.check_output(
            ["curl", "-sL", "--fail", "--max-time", "25", "-A", UA, url],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None


def is_image(data: bytes) -> bool:
    return len(data) > 8000 and data[:3] in (b"\xff\xd8\xff", b"\x89PN") or data[:4] == b"RIFF"


def candidate_urls(brand: str, model: str, color: str, badge: str) -> list[str]:
    brands = BRAND_SLUGS.get(brand.lower(), [slug(brand)])
    colors = COLOR_SLUGS.get(color.lower(), [slug(color)] if color else [""])
    models = [latin_model(model), slug(model), re.sub(r"[^a-z0-9]+", "", latin_model(model))]
    models = [m for m in models if m]
    urls: list[str] = []
    for b in brands:
        for m in models:
            urls.append(f"https://mosautoshina.ru/i/wheel/{b}-{m}.jpg")
            urls.append(f"https://mosautoshina.ru/i/wheel/{b}-{m}-max.jpg")
            for c in colors:
                if not c:
                    continue
                urls.append(f"https://mosautoshina.ru/i/wheel/{b}-{m}-{c}.jpg")
                urls.append(f"https://mosautoshina.ru/i/wheel/{b}-{m}-{c}-max.jpg")
                urls.append(f"https://mosautoshina.ru/i/wheel/{b}-{m}-{c}-400.jpg")
    # stamp / truck generics
    if badge == "Штамп":
        urls.extend(
            [
                "https://mosautoshina.ru/i/wheel/trebl-shtamp.jpg",
                "https://mosautoshina.ru/i/wheel/accuride.jpg",
            ]
        )
    return list(dict.fromkeys(urls))


def bing_urls(query: str) -> list[str]:
    page = curl_bytes(
        "https://www.bing.com/images/search?q="
        + urllib.parse.quote(query)
        + "&qft=+filterui:photo-photo+filterui:aspect-square&form=HDRSC2"
    )
    if not page:
        return []
    html = page.decode("utf-8", "ignore")
    found = []
    for raw in re.findall(r"murl&quot;:&quot;(https?://[^&]+)", html):
        found.append(urllib.parse.unquote(raw.replace("\\u0026", "&")))
    return found


def fit_wheel(src: Path, dest_stem: str) -> Path | None:
    try:
        im = Image.open(src)
    except Exception:
        return None
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im.convert("RGBA")).convert("RGB")
    else:
        im = im.convert("RGB")
    arr = np.array(im)
    h, w = arr.shape[:2]
    gray = arr.mean(2)

    # Prefer non-white content
    content = (gray < 245).astype(np.uint8) * 255
    content = cv2.morphologyEx(content, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), 2)
    n, lab, st, _ = cv2.connectedComponentsWithStats(content, 8)
    if n < 2:
        return None
    main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    if st[main, cv2.CC_STAT_AREA] < (h * w) * 0.02:
        return None
    ys, xs = np.where(lab == main)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    # wipe soft outside
    mask = lab == main
    pad = cv2.dilate(mask.astype(np.uint8) * 255, np.ones((5, 5), np.uint8), 2) > 0
    out = arr.copy()
    out[~pad] = (255, 255, 255)
    soft = (gray > 200) & (gray < 250) & ~pad
    out[soft] = (255, 255, 255)

    crop = Image.fromarray(out).crop((max(0, x0 - 8), max(0, y0 - 8), min(w, x1 + 9), min(h, y1 + 9)))
    tw, th = crop.size
    scale = min((TW * FILL) / tw, (TH * FILL) / th)
    nw, nh = max(1, int(tw * scale)), max(1, int(th * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    crop = ImageEnhance.Sharpness(crop).enhance(1.05)
    canvas = Image.new("RGB", (TW, TH), (255, 255, 255))
    x = (TW - nw) // 2
    y = max(40, min(TH - nh - 80, int((TH - nh) * 0.35)))
    canvas.paste(crop, (x, y))

    PUBLIC.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)
    BACKEND.mkdir(parents=True, exist_ok=True)
    full = PUBLIC / f"{dest_stem}.jpg"
    thumb = PUBLIC / f"{dest_stem}-thumb.jpg"
    canvas.save(full, "JPEG", quality=90, optimize=True)
    thimg = canvas.copy()
    thimg.thumbnail((360, 480))
    thimg.save(thumb, "JPEG", quality=85, optimize=True)
    for d in (DIST, BACKEND):
        (d / f"{dest_stem}.jpg").write_bytes(full.read_bytes())
        (d / f"{dest_stem}-thumb.jpg").write_bytes(thumb.read_bytes())
    return full


def download_group(brand: str, model: str, color: str, badge: str, stem: str) -> Path | None:
    TMP.mkdir(parents=True, exist_ok=True)
    raw = TMP / f"{stem}-raw.bin"
    # 1) direct mosautoshina candidates
    for url in candidate_urls(brand, model, color, badge):
        data = curl_bytes(url)
        if data and is_image(data):
            raw.write_bytes(data)
            out = fit_wheel(raw, stem)
            if out:
                print(f"  OK mosa {stem} <- {url}")
                return out
    # 2) bing search
    queries = [
        f"{brand} {model} {color} диск",
        f"{brand} {model} диск литой",
        f"{brand} {model} wheel",
    ]
    if badge == "Штамп":
        queries = [f"штампованный диск {color or 'серебристый'} авто", f"steel wheel rim silver"]
    if badge == "Грузовой":
        queries = [f"грузовой диск {model}", "truck steel wheel rim"]

    for q in queries:
        for url in bing_urls(q)[:12]:
            if any(x in url.lower() for x in (".svg", "logo", "icon", "sprite")):
                continue
            data = curl_bytes(url)
            if data and is_image(data):
                raw.write_bytes(data)
                out = fit_wheel(raw, stem)
                if out:
                    print(f"  OK bing {stem} <- {url[:90]}")
                    return out
        time.sleep(0.4)
    print(f"  MISS {stem} ({brand} {model} {color})")
    return None


def main() -> None:
    text = PRODUCTS.read_text(encoding="utf-8")
    disks = parse_disks(text)
    groups: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    meta: dict[tuple[str, str, str, str], dict] = {}
    for d in disks:
        key = (d["brand"], d["model"], d["badge"], d["color"])
        groups[key].append(d["id"])
        meta[key] = d

    print(f"products={len(disks)} groups={len(groups)}")
    mapping: dict[str, str] = {}  # product id -> /wheels/stem.jpg
    ok = miss = 0

    for i, (key, ids) in enumerate(sorted(groups.items(), key=lambda x: x[0]), 1):
        brand, model, badge, color = key
        d = meta[key]
        stem = d["id"]
        print(f"[{i}/{len(groups)}] {brand} | {model} | {color or '-'} | {badge}")
        # reuse if already fitted
        existing = PUBLIC / f"{stem}.jpg"
        if existing.exists() and existing.stat().st_size > 5000:
            path = existing
            print(f"  SKIP existing {stem}")
        else:
            path = download_group(brand, model, color, badge, stem)
        if path:
            ok += 1
            rel = f"/wheels/{stem}.jpg"
            for pid in ids:
                mapping[pid] = rel
        else:
            miss += 1
        time.sleep(0.15)

    # write image fields into products.ts for disk entries
    new_text = text
    for pid, rel in mapping.items():
        # insert image after imageKey: 'disk' inside that product block
        pattern = rf"(id: '{re.escape(pid)}',[\s\S]*?imageKey: 'disk',)"
        repl = rf"\1\n    image: '{rel}',"
        if f"image: '{rel}'" in new_text and pid in new_text:
            # maybe already has image — replace existing image line in block
            block_pat = rf"(id: '{re.escape(pid)}',[\s\S]*?)(image: '[^']*',\n)?"
            # simpler: if image already near id, replace
            pass
        if re.search(rf"id: '{re.escape(pid)}'[\s\S]{{0,400}}image:", new_text):
            new_text = re.sub(
                rf"(id: '{re.escape(pid)}'[\s\S]{{0,450}}?)image: '[^']*',",
                rf"\1image: '{rel}',",
                new_text,
                count=1,
            )
        else:
            new_text = re.sub(pattern, repl, new_text, count=1)

    if new_text != text:
        PRODUCTS.write_text(new_text, encoding="utf-8")
        PRODUCTS.touch()
        print(f"products.ts updated: {len(mapping)} images wired")
    print(f"done ok={ok} miss={miss}")


if __name__ == "__main__":
    main()
