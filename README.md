# Kcal Diary

A single-page calorie log: day total against a target range, one-tap regular meals and items, and a 14-day history.

Open it at https://perhoinc.github.io/kcal-diary/

The log is stored in the browser's local storage on each device. Nothing is stored in this repository. Use **Backup → Export backup** to save a copy, and **Import backup** to restore it or move it to another device.

## Installing and updating

On iPhone: open the address in Safari, then Share, then Add to Home Screen. The home-screen app has its own storage, so import a backup there once.

The app works offline. Before pushing any change to a file, bump `VERSION` in `sw.js` so installed copies download the new files.
