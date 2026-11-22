# Kcal Diary

A single-page calorie log: day total against a target range, one-tap regular meals and items, and a 14-day history.

Open it at https://perhoinc.github.io/kcal-diary/

The log is stored in the browser's local storage on each device. Nothing is stored in this repository. Use **Backup → Export backup** to save a copy, and **Import backup** to restore it or move it to another device.

## Installing and updating

On iPhone: open the address in Safari, then Share, then Add to Home Screen. The home-screen app has its own storage, so import a backup there once.

The app works offline. Before pushing any change to a file, bump `VERSION` in `sw.js` so installed copies download the new files.

## Food data

`foods.json` is a trimmed copy of the Swedish Food Composition Database (Livsmedelsdatabasen) from Livsmedelsverket, the Swedish Food Agency, published under the Creative Commons Attribution 4.0 licence. It holds each food's Swedish name and its kcal, protein, fat, carbohydrates and fibre per 100 g.

`products-se.json` holds the products sold in Sweden from Open Food Facts (openfoodfacts.org), with name, brand, pack size and kcal, protein, fat, carbohydrates and fibre per 100 g (per 100 ml for drinks). It is a derived database of Open Food Facts and is available under the Open Database License (ODbL).

Both are fetched by `tools/fetch_foods.py` and `tools/fetch_off.py`, which GitHub runs from `.github/workflows/foods.yml` on the 1st of each month, whenever those files change, or by hand from the Actions tab (Update food database › Run workflow). `tools/foods-log.txt` and `tools/off-log.txt` show what the last run did.

`matches.json` lists suggested database matches for the regular items in the log, by item id only (a Livsmedelsverket food id or an Open Food Facts barcode). Edit › Nutrients from food databases shows them for review.
