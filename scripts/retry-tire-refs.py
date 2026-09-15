#!/usr/bin/env python3
"""Second pass for models missed by fetch-tire-refs.py."""

from __future__ import annotations

import html as html_lib
import re
import subprocess
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "reference-photos"
LOG = ROOT / "download-log.tsv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TR = str.maketrans(
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "abvgdeezziiklmnoprstufhccss_y_eua",
)
BAD_HOSTS = ("pinimg.com", "wallpaper", "gq.com", "emoji.gg", "britannica", "alamy", "nytimes", "vice.com")


def slug(value: str) -> str:
    value = value.lower().replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.I)
    return value.strip("-")[:80] or "model"


def latin(value: str) -> str:
    return value.lower().replace("ё", "е").translate(TR)


def curl(url: str) -> bytes:
    return subprocess.check_output(
        ["curl", "-sL", "--fail", "--max-time", "20", "-A", UA, url],
        stderr=subprocess.DEVNULL,
    )


def search_urls(query: str) -> list[str]:
    page = curl(
        "https://www.bing.com/images/search?q=" + urllib.parse.quote(query) + "&form=HDRSC2&first=1"
    ).decode("utf-8", "ignore")
    return [html_lib.unescape(raw) for raw in re.findall(r"murl&quot;:&quot;(https?://[^&]+)", page)]


def codes(model: str) -> list[str]:
    found = re.findall(r"[A-Za-zА-Яа-я]*\d+[A-Za-zА-Яа-я0-9-]*", model)
    out = []
    for item in found:
        low = item.lower().replace("ё", "е")
        if low not in {"8pr", "16pr"} and not re.fullmatch(r"\d{2,3}", low):
            out.append(low.replace("-", ""))
            out.append(latin(low).replace("-", ""))
    return [item for item in out if len(item) >= 3]


def looks_like_tire(url: str) -> bool:
    low = url.lower()
    if any(host in low for host in BAD_HOSTS):
        return False
    if any(part in low for part in (".svg", "logo", "/anfas/", "/protector/")):
        return False
    return any(
        part in low
        for part in (
            "tyre", "tire", "pneu", "shin", "koles", "wheel", "mosautoshina",
            "4tochki", "belshina", "kama", "кама",
        )
    )


def is_image(data: bytes) -> bool:
    return (
        data[:3] == b"\xff\xd8\xff"
        or data[:8] == b"\x89PNG\r\n\x1a\n"
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )


def misses() -> list[tuple[str, str]]:
    rows = []
    for line in LOG.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0] == "miss":
            rows.append((parts[1], parts[2]))
    return rows


def main() -> None:
    rows = misses()
    print(f"retry {len(rows)}", flush=True)
    ok = 0
    with LOG.open("a", encoding="utf-8") as log:
        for index, (brand, model) in enumerate(rows, 1):
            dest = ROOT / slug(brand) / f"{slug(model)}.jpg"
            if dest.exists() and dest.stat().st_size > 8000:
                continue
            query = f"{latin(brand)} {latin(model)} tire"
            try:
                urls = search_urls(f"{brand} {model} шина site:mosautoshina.ru")
                urls += search_urls(query)
            except Exception as error:  # noqa: BLE001
                print(f"[{index}] ERR {brand} {model}: {error}", flush=True)
                continue
            wanted = codes(model)
            saved = False
            for url in urls:
                compact = url.lower().replace("-", "").replace("_", "")
                if wanted and not any(code in compact for code in wanted):
                    continue
                if not looks_like_tire(url):
                    continue
                try:
                    data = curl(url)
                except Exception:
                    continue
                if len(data) < 8000 or not is_image(data):
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                ok += 1
                saved = True
                log.write(f"retry\t{brand}\t{model}\t{dest.relative_to(ROOT)}\t{url}\n")
                log.flush()
                print(f"[{index}/{len(rows)}] OK {brand} {model}", flush=True)
                break
            if not saved:
                print(f"[{index}/{len(rows)}] MISS {brand} {model}", flush=True)
    print(f"RETRY DONE ok={ok}", flush=True)


if __name__ == "__main__":
    main()
