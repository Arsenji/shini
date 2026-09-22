#!/usr/bin/env python3
"""Rematch missing tire photos from public/tires/*.jpg by brand/model slug."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_TS = ROOT / "src/data/shop/products.ts"
TIRES_DIR = ROOT / "public/tires"


CYR_MAP = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "c",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)


def slugify(text: str) -> str:
    t = text.lower().replace("\\", "/").replace("ё", "е")
    t = re.sub(r"[х×]", "x", t)
    # Cyrillic brand aliases → latin file stems
    repl = {
        "кама": "kama",
        "белшина": "belshina",
        "волтайр": "voltyre",
        "амтел": "amtel",
        "кордиант": "cordiant",
        "westlaik": "westlake",
        "goodraid": "goodride",
        "three-a": "three-a",
        "three a": "three-a",
    }
    for a, b in repl.items():
        t = t.replace(a, b)
    t = t.translate(CYR_MAP)
    t = re.sub(r"[^a-z0-9._-]+", "-", t, flags=re.I)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t


def load_catalog() -> list[dict]:
    script = (
        "import { shopProducts } from './src/data/shop/products.ts'; "
        "import fs from 'fs'; "
        "fs.writeFileSync('.tmp-catalog.json', JSON.stringify(shopProducts))"
    )
    subprocess.check_call(["node", "--import", "tsx", "-e", script], cwd=ROOT)
    return json.loads((ROOT / ".tmp-catalog.json").read_text(encoding="utf-8"))


def tire_stems() -> list[str]:
    stems: list[str] = []
    for p in TIRES_DIR.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".jpg", ".jpeg", ".webp", ".png"}:
            continue
        if "-thumb" in p.stem:
            continue
        # prefer jpg over png when both exist — handled at path resolve
        stems.append(p.stem.lower())
    # unique preferring order
    seen: set[str] = set()
    out: list[str] = []
    for s in stems:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def resolve_image_path(stem: str) -> str | None:
    for ext in (".jpg", ".jpeg", ".webp", ".png"):
        if (TIRES_DIR / f"{stem}{ext}").is_file():
            return f"/tires/{stem}{ext}"
    return None


LOAD_TOKEN = re.compile(r"^\d{2,3}(?:/\d{2,3})?[A-Za-zА-Яа-я]$")
# 205/55R16, 8.25R20, 11R22.5, R16C, 50R16 leftovers
SIZE_LIKE = re.compile(
    r"^(\d{1,3}([./]\d{1,3})?R\d{1,2}(\.\d)?[Cc]?|\d{2,3}(/\d{2,3})?R\d{1,2}[Cc]?)$",
    re.I,
)
JUNK = {
    "шип",
    "шипы",
    "лип",
    "липучка",
    "xl",
    "tl",
    "tt",
    "ttf",
    "pr",
    "шт",
    "н/к",
    "нкшз",
    "бм",
    "омск",
    "волжск",
    "барнаул",
    "унив",
    "универ",
    "сл",
}


def meaningful_tokens(brand: str, model: str) -> list[str]:
    raw = f"{brand} {model}"
    parts = re.split(r"[\s/_,;|()]+", raw)
    # join lone letter + number: "О" "40" → "О-40"
    merged: list[str] = []
    i = 0
    while i < len(parts):
        a = parts[i].strip().strip(".")
        b = parts[i + 1].strip().strip(".") if i + 1 < len(parts) else ""
        if re.fullmatch(r"[A-Za-zА-Яа-я]{1,3}", a) and re.fullmatch(r"\d{1,4}[A-Za-zА-Яа-я]?", b):
            merged.append(f"{a}-{b}")
            i += 2
            continue
        if a:
            merged.append(a)
        i += 1
    out: list[str] = []
    for p in merged:
        # Mixed Cyrillic/Latin model codes: СM954 → CM954
        if re.search(r"[A-Za-z]", p) and re.search(r"[А-Яа-яЁё]", p):
            p = (
                p.replace("С", "C")
                .replace("с", "c")
                .replace("А", "A")
                .replace("Е", "E")
                .replace("О", "O")
                .replace("Р", "P")
                .replace("К", "K")
                .replace("М", "M")
                .replace("Н", "H")
                .replace("В", "B")
                .replace("Т", "T")
                .replace("Х", "X")
            )
        if not p or len(p) < 2:
            continue
        if LOAD_TOKEN.match(p):
            continue
        if SIZE_LIKE.match(p):
            continue
        if re.fullmatch(r"\d+сл", p, re.I):
            continue
        if p.lower() in JUNK:
            continue
        out.append(p)
    return out


def candidate_queries(brand: str, model: str) -> list[str]:
    toks = meaningful_tokens(brand, model)
    queries: list[str] = []
    # full brand as-is (handles "Aplus A609", "Кама-241", "Cordiant Sport 2")
    queries.append(slugify(brand))
    if toks:
        queries.append(slugify(" ".join(toks[:4])))
        queries.append(slugify(f"{brand} {toks[0]}"))
    if len(toks) >= 2:
        queries.append(slugify(f"{toks[0]} {toks[1]}"))
        brand_first = brand.split()[0] if brand.split() else brand
        queries.append(slugify(f"{brand_first} {toks[0]}"))
        queries.append(slugify(f"{brand_first} {toks[1]}"))
    # model-only codes like ES31, W429, НК-240, О-79, И-281
    for t in toks:
        if re.search(r"[A-Za-zА-Яа-я].*\d|\d.*[A-Za-zА-Яа-я]", t) or re.match(
            r"^[A-Za-zА-Яа-я]{1,4}-\d", t
        ):
            brand_first = brand.split()[0] if brand.split() else brand
            queries.append(slugify(f"{brand_first} {t}"))
            queries.append(slugify(t))
            # truck Excel lines often put size as brand → assume Kama for RU codes
            sl = slugify(t)
            if re.match(r"^(nk|o|oi|u|i|in|f)-\d|^[a-z]{1,3}-\d", sl):
                queries.append(f"kama-{sl}")
                queries.append(sl)
    # known brand+code pairs from mixed Excel lines
    joined = slugify(" ".join(toks))
    for brand_key, codes in (
        ("hifly", ("hh301", "hh102", "hh107", "hh308a")),
        ("huasheng", ("hs268",)),
        ("goodride", ("cm954",)),
        ("three-a", ("a168", "a-168", "p306")),
        ("westlake", ("cm954",)),
    ):
        if brand_key in joined or any(slugify(t) == brand_key for t in toks):
            for c in codes:
                if c.replace("-", "") in joined.replace("-", ""):
                    queries.append(f"{brand_key}-{c.replace('-', '')}")
                    queries.append(f"{brand_key}-{c}")
    # dedupe
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        q = q.strip("-")
        if q and q not in seen and len(q) >= 3:
            seen.add(q)
            out.append(q)
    return out


def best_stem(queries: list[str], stems: list[str]) -> str | None:
    # exact
    stem_set = set(stems)
    for q in queries:
        if q in stem_set:
            return q
    # stem startswith query or query startswith stem
    for q in queries:
        hits = [s for s in stems if s.startswith(q) or q.startswith(s)]
        if len(hits) == 1:
            return hits[0]
        if hits:
            # shortest close match
            hits.sort(key=lambda s: (abs(len(s) - len(q)), len(s)))
            if abs(len(hits[0]) - len(q)) <= 8:
                return hits[0]
    # contains all query tokens
    for q in queries:
        parts = [p for p in q.split("-") if len(p) >= 2]
        if len(parts) < 2:
            continue
        hits = [s for s in stems if all(p in s for p in parts[:3])]
        if len(hits) == 1:
            return hits[0]
        if hits:
            hits.sort(key=len)
            return hits[0]
    return None


def ts_str(value: object) -> str:
    if value is None:
        return "null"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def render_product(p: dict) -> str:
    lines = [
        "  {",
        f"    id: {ts_str(p['id'])},",
        f"    brand: {ts_str(p['brand'])},",
        f"    model: {ts_str(p['model'])},",
        f"    category: {ts_str(p['category'])},",
    ]
    if p.get("season"):
        lines.append(f"    season: {ts_str(p['season'])},")
    lines.append(f"    imageKey: {ts_str(p['imageKey'])},")
    if p.get("sizeGroup"):
        lines.append(f"    sizeGroup: {ts_str(p['sizeGroup'])},")
    if p.get("sizes"):
        lines.append(f"    sizes: [{', '.join(ts_str(s) for s in p['sizes'])}],")
    if p.get("badge"):
        lines.append(f"    badge: {ts_str(p['badge'])},")
    if p.get("stockRemaining"):
        lines.append(f"    stockRemaining: {int(p['stockRemaining'])},")
    if p.get("image"):
        lines.append(f"    image: {ts_str(p['image'])},")
    if p.get("color"):
        lines.append(f"    color: {ts_str(p['color'])},")
    if p.get("truckSpecs"):
        lines.append(f"    truckSpecs: {ts_str(p['truckSpecs'])},")
    if p.get("plyRating"):
        lines.append(f"    plyRating: {ts_str(p['plyRating'])},")
    if p.get("loadIndex"):
        lines.append(f"    loadIndex: {ts_str(p['loadIndex'])},")
    if isinstance(p.get("price"), (int, float)):
        lines.append(f"    price: {int(p['price'])},")
    if p.get("offers"):
        lines.append("    offers: [")
        for o in p["offers"]:
            lines.append(f"      {{ size: {ts_str(o['size'])}, price: {int(o['price'])} }},")
        lines.append("    ],")
    lines.append("  }")
    return "\n".join(lines)


def main() -> None:
    products = load_catalog()
    stems = tire_stems()
    print(f"catalog={len(products)} tire_stems={len(stems)}")

    filled = 0
    still = 0
    examples: list[str] = []
    for p in products:
        if p.get("category") not in {"passenger", "lcv", "truck"}:
            continue
        if p.get("image"):
            continue
        queries = candidate_queries(str(p.get("brand") or ""), str(p.get("model") or ""))
        stem = best_stem(queries, stems)
        if not stem:
            still += 1
            if len(examples) < 12:
                examples.append(f"{p.get('brand')} | {p.get('model')} ← {queries[:3]}")
            continue
        path = resolve_image_path(stem)
        if not path:
            still += 1
            continue
        p["image"] = path
        filled += 1

    header = """import type { ShopProduct } from './types'

/**
 * Каталог магазина.
 * Шины (passenger/lcv/truck) — автогенерация: scripts/rebuild-tires-from-excel.py
 * Диски / камеры / ободные ленты сохраняются из предыдущего каталога.
 */
export const shopProducts: ShopProduct[] = [
"""
    PRODUCTS_TS.write_text(header + ",\n".join(render_product(p) for p in products) + "\n]\n", encoding="utf-8")
    print(f"filled={filled} still_missing={still}")
    for e in examples:
        print("  miss:", e)


if __name__ == "__main__":
    main()
