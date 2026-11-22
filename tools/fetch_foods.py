#!/usr/bin/env python3
"""Fetch the Swedish Food Composition Database (Livsmedelsverket, CC BY 4.0) and save a
trimmed copy for Kcal Diary: Swedish name, kcal, protein, fat, carbs and fibre per 100 g.

Runs on GitHub's servers (see .github/workflows/foods.yml). Writes foods.json for the app
and tools/foods-log.txt with what happened, so a failed run can be read from the repo.
"""
import json, sys, time, datetime, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = "https://dataportal.livsmedelsverket.se/livsmedel/api/v1"
LOG = []
def log(*a):
    line = " ".join(str(x) for x in a); LOG.append(line); print(line, flush=True)

def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "kcal-diary-food-db"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))

def as_list(obj, keys):
    """The API may answer with a bare list or wrap it in an object."""
    if isinstance(obj, list): return obj
    if isinstance(obj, dict):
        for k in keys:
            for kk in obj:
                if kk.lower() == k and isinstance(obj[kk], list): return obj[kk]
        for v in obj.values():
            if isinstance(v, list): return v
    return []

def field(d, *names):
    low = {k.lower(): v for k, v in d.items()}
    for n in names:
        if n.lower() in low: return low[n.lower()]
    return None

def num(v):
    if v is None or v == "": return None
    try: return float(str(v).replace(",", ".").replace(" ", "").strip())
    except ValueError: return None

# Nutrient codes (EuroFIR) we keep, with fallbacks on the Swedish names
WANT = {
    "kcal": (["ENERC"], ["energi (kcal)", "energy (kcal)"]),
    "p":    (["PROT"], ["protein"]),
    "f":    (["FAT"], ["fett, totalt", "fett", "fat, total"]),
    "c":    (["CHO", "CHOAVL"], ["kolhydrater, tillgängliga", "kolhydrater", "carbohydrates, available"]),
    "fib":  (["FIBT", "FIBTG"], ["fibrer", "fiber", "dietary fibre"]),
}

def pick(nutrients):
    out = {}
    for key, (codes, names) in WANT.items():
        for n in nutrients:
            code = str(field(n, "euroFIRkod", "forkortning") or "").upper()
            name = str(field(n, "namn") or "").lower().strip()
            unit = str(field(n, "enhet") or "").lower()
            if key == "kcal" and "kj" in unit: continue
            if key == "kcal" and code == "ENERC" and unit and "kcal" not in unit: continue
            if code in codes or name in names:
                v = num(field(n, "varde", "värde"))
                if v is not None: out[key] = round(v, 1); break
    return out

def main():
    started = datetime.datetime.now(datetime.timezone.utc)
    log("Started", started.isoformat())
    try:
        info = get(BASE.replace("/v1", "/") if False else "https://dataportal.livsmedelsverket.se/livsmedel/api/")
        log("API info:", json.dumps(info, ensure_ascii=False)[:400])
    except Exception as e:
        log("API info failed:", repr(e))
    foods, offset, limit = [], 0, 500
    while True:
        url = f"{BASE}/livsmedel?offset={offset}&limit={limit}&sprak=1"
        raw = get(url)
        if offset == 0: log("First list page (start):", json.dumps(raw, ensure_ascii=False)[:600])
        page = as_list(raw, ["livsmedel", "items", "data"])
        foods += page
        log(f"offset {offset}: {len(page)} foods")
        if len(page) < limit or offset > 20000: break
        offset += limit
    log("Foods listed:", len(foods))
    if not foods:
        raise SystemExit("No foods in the list")
    first = foods[0]
    log("First food fields:", json.dumps(first, ensure_ascii=False)[:400])

    def one(f):
        nr = field(f, "nummer", "id")
        name = field(f, "namn", "name")
        try:
            nut = as_list(get(f"{BASE}/livsmedel/{nr}/naringsvarden?sprak=1"), ["naringsvarden", "items", "data"])
        except Exception as e:
            return nr, name, None, repr(e)
        return nr, name, nut, None

    rows, errors, sample_logged = [], 0, False
    with ThreadPoolExecutor(max_workers=8) as ex:
        for nr, name, nut, err in ex.map(one, foods):
            if err: errors += 1; continue
            if not sample_logged:
                log("Nutrients of first food:", json.dumps([{k: field(n, k) for k in ("namn", "euroFIRkod", "forkortning", "varde", "enhet")} for n in nut][:60], ensure_ascii=False)[:3000])
                sample_logged = True
            v = pick(nut)
            if not name or v.get("kcal") is None: continue
            rows.append([int(nr) if str(nr).isdigit() else nr, str(name).strip(), v.get("kcal"), v.get("p"), v.get("f"), v.get("c"), v.get("fib")])
    rows.sort(key=lambda r: r[1].lower())
    log(f"Kept {len(rows)} foods, {errors} errors")
    if len(rows) < 1000:
        log("Too few foods, foods.json left as it was")
        return
    out = {"source": "Livsmedelsverket, Livsmedelsdatabasen", "license": "CC BY 4.0", "fetched": started.strftime("%Y-%m-%d"),
           "per": "100 g", "cols": ["id", "name", "kcal", "p", "f", "c", "fib"], "rows": rows}
    with open("foods.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    log("Wrote foods.json")

if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        log("FAILED:", repr(e))
    finally:
        with open("tools/foods-log.txt", "w", encoding="utf-8") as fh:
            fh.write("\n".join(LOG) + "\n")
