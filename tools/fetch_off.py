#!/usr/bin/env python3
"""Build products-se.json for Kcal Diary: products sold in Sweden from Open Food Facts (ODbL),
with name, brand, pack size and kcal, protein, fat, carbs and fibre per 100 g (or 100 ml for drinks).

Runs on GitHub's servers (see .github/workflows/foods.yml). Streams Open Food Facts' full CSV export
and keeps only Swedish products that have kcal. Writes tools/off-log.txt with what happened.
"""
import csv, gzip, io, json, re, sys, time, datetime, urllib.request

URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
LOG = []
def log(*a):
    line = " ".join(str(x) for x in a); LOG.append(line); print(line, flush=True)

def num(v):
    if v is None or v == "": return None
    try:
        x = float(v)
        return x if x == x and abs(x) < 1e6 else None
    except ValueError:
        return None

def main():
    t0 = time.time(); started = datetime.datetime.now(datetime.timezone.utc)
    log("Started", started.isoformat())
    csv.field_size_limit(sys.maxsize)
    req = urllib.request.Request(URL, headers={"User-Agent": "KcalDiary/1.0 (github.com/Perhoinc/kcal-diary; monthly export)"})
    rows, seen, total, swedish = [], set(), 0, 0
    with urllib.request.urlopen(req, timeout=600) as r:
        text = io.TextIOWrapper(gzip.GzipFile(fileobj=r), encoding="utf-8", errors="replace", newline="")
        rd = csv.DictReader(text, delimiter="\t", quoting=csv.QUOTE_NONE)
        log("Columns found:", ", ".join(c for c in (rd.fieldnames or []) if c in ("code","product_name","brands","quantity","product_quantity_unit","countries_tags","energy-kcal_100g","energy_100g","proteins_100g","fat_100g","carbohydrates_100g","fiber_100g")))
        for row in rd:
            total += 1
            if "en:sweden" not in (row.get("countries_tags") or ""): continue
            swedish += 1
            name = (row.get("product_name") or "").strip()
            kcal = num(row.get("energy-kcal_100g"))
            if kcal is None:
                kj = num(row.get("energy_100g")); kcal = kj / 4.184 if kj is not None else None
            if not name or kcal is None or kcal > 950: continue
            brand = (row.get("brands") or "").split(",")[0].strip()
            key = (name.lower(), brand.lower())
            if key in seen: continue
            seen.add(key)
            qty = (row.get("quantity") or "").strip()[:20]
            unit = (row.get("product_quantity_unit") or "").strip().lower()
            liquid = 1 if unit in ("ml", "cl", "l") or re.search(r"\d\s*(ml|cl|l)\b", qty, re.I) else 0
            r1 = lambda v: None if v is None else round(v, 1)
            rows.append([row.get("code") or "", name[:80], brand[:40], qty, liquid, round(kcal),
                         r1(num(row.get("proteins_100g"))), r1(num(row.get("fat_100g"))), r1(num(row.get("carbohydrates_100g"))), r1(num(row.get("fiber_100g")))])
            if total % 500000 == 0: log(f"... {total} rows read, {len(rows)} kept")
    log(f"Rows read: {total}, sold in Sweden: {swedish}, kept: {len(rows)}, {round(time.time()-t0)} s")
    if len(rows) < 1000:
        log("Too few products, products-se.json left as it was"); return
    rows.sort(key=lambda r: (r[1].lower(), r[2].lower()))
    out = {"source": "Open Food Facts", "license": "ODbL", "fetched": started.strftime("%Y-%m-%d"), "per": "100 g, or 100 ml when liquid is 1",
           "cols": ["code", "name", "brand", "quantity", "liquid", "kcal", "p", "f", "c", "fib"], "rows": rows}
    with open("products-se.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    import os
    log("Wrote products-se.json,", os.path.getsize("products-se.json"), "bytes")

if __name__ == "__main__":
    try: main()
    except BaseException as e: log("FAILED:", repr(e))
    finally:
        with open("tools/off-log.txt", "w", encoding="utf-8") as fh: fh.write("\n".join(LOG) + "\n")
