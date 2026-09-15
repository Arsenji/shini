#!/usr/bin/env python3
"""Download photography references for tire models missing catalog photos.

Sources are retail product photos used only as pose references, not for the site.
"""

from __future__ import annotations

import html as html_lib
import re
import subprocess
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "reference-photos"
TSV = ROOT / "models-without-photos.tsv"
LOG = ROOT / "download-log.tsv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def slug(value: str) -> str:
    value = value.lower().replace("ё", "е").replace("\\", " ").replace("/", "-")
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.I)
    return value.strip("-")[:80] or "model"


def norm(value: str) -> str:
    return re.sub(r"[^a-zа-я0-9]+", "", value.lower().replace("ё", "е"))


def clean_model(model: str) -> str:
    cleaned = re.sub(
        r"\b(\d{2,3}/\d{2}r?\d{1,2}c?|\d{2,3}r\d{2}c?|\dшт|8pr|16pr|нс8|н/с8)\b.*$",
        "",
        model,
        flags=re.I,
    )
    return re.sub(r"\s+", " ", cleaned).strip() or model.strip()


def targets() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in TSV.read_text(encoding="utf-8").splitlines()[1:]:
        if not line.strip():
            continue
        category, _season, brand, model = line.split("\t", 3)
        model = model.strip()
        key = (norm(brand), norm(clean_model(model)), "lcv" if category == "lcv" else "passenger")
        if key in seen:
            continue
        seen.add(key)
        rows.append((brand, model))
    return rows


def curl(url: str) -> bytes:
    return subprocess.check_output(
        ["curl", "-sL", "--fail", "--max-time", "20", "-A", UA, url],
        stderr=subprocess.DEVNULL,
    )


def search_urls(query: str) -> list[str]:
    page = curl(
        "https://www.bing.com/images/search?q="
        + urllib.parse.quote(query)
        + "&form=HDRSC2&first=1"
    ).decode("utf-8", "ignore")
    urls = []
    for raw in re.findall(r"murl&quot;:&quot;(https?://[^&]+)", page):
        urls.append(html_lib.unescape(raw))
    return urls


STUDIO = (
    "mosautoshina.ru/i/tyre/",
    "4tochki.ru",
    "img-slik.ru",
    "kolesa-darom",
    "shiny.ru",
    "blacktyres",
    "shinamax.ru",
)
GENERIC = {
    "шина", "tire", "tyre", "500", "max", "2x", "lcv", "van", "cargo",
    "commercial", "lt", "new", "plus",
}


def model_tokens(model: str) -> list[str]:
    tokens: list[str] = []
    for part in re.findall(r"[A-Za-zА-Яа-я0-9]+", clean_model(model)):
        low = part.lower().replace("ё", "е")
        if low in GENERIC or re.fullmatch(r"\d+", low):
            continue
        if len(low) >= 3 or re.search(r"\d", low) or part.isupper():
            tokens.append(low)
    return tokens


def matches(url: str, model: str) -> bool:
    low = url.lower().replace("_", "-")
    tokens = model_tokens(model)
    if not tokens:
        return True
    return all(token in low for token in tokens)


def score(url: str, brand: str, model: str) -> int:
    low = url.lower()
    if any(part in low for part in (".svg", "logo", "icon", "sprite", "favicon", "/anfas/")):
        return -1
    if not matches(url, model):
        return -1
    points = 0
    if "mosautoshina.ru/i/tyre/" in low:
        points += 40
    elif any(host in low for host in STUDIO):
        points += 16
    if brand.lower().split()[0] in low:
        points += 2
    if any(ext in low for ext in (".jpg", ".jpeg", ".png", ".webp")):
        points += 1
    return points


def is_image(data: bytes) -> bool:
    return (
        data[:3] == b"\xff\xd8\xff"
        or data[:8] == b"\x89PNG\r\n\x1a\n"
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )


def main() -> None:
    for old in ROOT.rglob("*.jpg"):
        old.unlink()
    rows = targets()
    print(f"unique targets {len(rows)}", flush=True)
    ok = skip = fail = 0
    with LOG.open("w", encoding="utf-8") as log:
        log.write("status\tbrand\tmodel\tfile\turl\n")
        for index, (brand, model) in enumerate(rows, 1):
            folder = ROOT / slug(brand)
            folder.mkdir(parents=True, exist_ok=True)
            dest = folder / f"{slug(model)}.jpg"
            query = f"{brand} {clean_model(model)} шина site:mosautoshina.ru"
            try:
                urls = search_urls(query)
                if not any(score(url, brand, model) >= 16 for url in urls):
                    urls += search_urls(f"{brand} {clean_model(model)} шина")
            except Exception as error:  # noqa: BLE001
                fail += 1
                log.write(f"err\t{brand}\t{model}\t\t{error}\n")
                log.flush()
                print(f"[{index}/{len(rows)}] ERR {brand} {model}: {error}", flush=True)
                continue
            ranked = sorted(urls, key=lambda url: score(url, brand, model), reverse=True)
            saved = False
            for url in ranked[:8]:
                if score(url, brand, model) < 1:
                    continue
                try:
                    data = curl(url)
                except Exception:
                    continue
                if len(data) < 8000 or not is_image(data):
                    continue
                dest.write_bytes(data)
                ok += 1
                saved = True
                log.write(f"ok\t{brand}\t{model}\t{dest.relative_to(ROOT)}\t{url}\n")
                log.flush()
                print(f"[{index}/{len(rows)}] OK {brand} {model} ({len(data) // 1024} KB)", flush=True)
                break
            if not saved:
                fail += 1
                log.write(f"miss\t{brand}\t{model}\t\t{ranked[0] if ranked else ''}\n")
                log.flush()
                print(f"[{index}/{len(rows)}] MISS {brand} {model}", flush=True)
            time.sleep(0.3)
    print(f"DONE ok={ok} skip={skip} fail={fail}", flush=True)


if __name__ == "__main__":
    main()
