# TUİK Grid Scraper

This repository automates the collection of square-grid data from the [Turkish Statistical Institute (TÜİK) map portal](https://cip.tuik.gov.tr/).  
It combines Selenium-driven browser automation with a systematic coordinate generator so you can walk the map tile-by-tile, capture the grid metadata that TÜİK renders in the browser, and save it to CSV for downstream analysis.

---

## Key Features

- **Automated map control** – launches a Chrome window, focuses the TÜİK map, and recenters/zooms to each target coordinate.
- **Systematic sampling** – generates evenly spaced latitude/longitude pairs inside any selected province ("il") or for the whole country.
- **In-browser data capture** – injects helper JavaScript to read the `grid_katmani` layer the site draws and extract the grid properties (ID, geometry, statistics, …).
- **Crash-safe resume** – if the destination CSV already exists, previously scraped grid squares are skipped so you can resume long-running jobs.
- **Optional visualisation** – plots the polygons and target points before scraping so you can sanity-check coverage.

---

## Repository Layout

```
tuik_grid_scrape/
├── scripts/run_script.py        # Command-line entry point for scraping
├── tuik_scraper/
│   ├── scraper.py               # Selenium workflow and data collection loop
│   ├── coordinate_generator.py  # GeoJSON loading and grid point generation
│   ├── js_injections.py         # JavaScript helpers executed in the browser
│   ├── utils.py                 # CSV writer, dedupe helper, visualiser
├── resources/                   # Province-level GeoJSON files
├── data/                        # Output folder for CSVs (created automatically)
└── requirements.txt             # Python dependencies
```

---

## Prerequisites

- Python 3.10+ (tested on CPython)
- Google Chrome installed locally (matching the Selenium-managed chromedriver)
- Node devtools familiarity: during scraping you must open Chrome DevTools to let the injected script hook into the map instance.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

> **Tip:** The requirements include optional macOS-specific packages for PyAutoGUI. They are marked with environment markers and will be skipped automatically on Linux/Windows.

---

## Quick Start

1. **Activate your environment**
   ```bash
   cd tuik_grid_scrape
   source <your-env>/bin/activate  # optional but recommended
   ```

2. **Run the scraper for one or more provinces**
   ```bash
   python scripts/run_script.py --il Yalova
   ```
   You can supply multiple provinces to cover them sequentially:
   ```bash
   python scripts/run_script.py --il Ankara "İstanbul" İzmir
   ```
   To scrape the whole of Türkiye (aggregated polygons at admin level 2), pass the literal string `Türkiye`:
   ```bash
   python scripts/run_script.py --il Türkiye
   ```

3. **Hook the map when prompted**
   - The script opens https://cip.tuik.gov.tr/ in Chrome and injects a hook script.
   - When you see the terminal prompt `👉 Please open DevTools...`:
     1. Press `Ctrl+Shift+I` / `Cmd+Option+I` to open DevTools.
     2. Wait for the console message `✅ Hooked map instance`.
     3. (If the hook message does not appear) set a temporary breakpoint in the minified file at the line containing `queryRenderedFeatures(e.point, { layers: ["grid_katmani"] })`, hover on the map to pause execution, then run `window.__my_map = i.map;` in the console once to expose the Mapbox map object.
     4. Return to the terminal and press `Enter` to continue.

4. **Let the automation run**
   - Selenium will iterate over every generated coordinate, zoom the map, collect the visible grid squares via the injected `CAPTURE_VISIBLE_GRID` script, and append the results to `data/tuik_grid_data_tr_20km.csv` (or the path you configure).
   - Progress messages show how many squares have been captured and the running timestamp.

5. **Inspect the results**
   - The output CSV contains one row per grid square with:
     - `id`: TÜİK grid identifier
     - `timestamp`: capture time (epoch ms)
     - `geometry`: polygon in WKT format
     - `lon_lat`: centre point used to trigger the capture
     - Additional TÜİK-provided properties (population, dwelling counts, etc.)
   - Re-run the scraper to resume; previously saved `lon_lat` values are filtered out before scraping.

---

## Configuration & Customisation

- **Output location** – pass a custom `output_path` when calling `scrape_tuik` programmatically. The directory is created automatically and large files are rotated once they reach ~2 GB.
- **Grid spacing** – adjust the `aralik` argument inside `coordinate_generator.generate_grid` (default 5,000 m). Smaller values increase coverage density and runtime.
- **Zoom level & delay** – tweak the `zoom` and `delay` parameters of `start_grid_capture` in `scraper.py` if you need to give the site more time to render tiles on slower connections.
- **Visual checks** – set the `visualize` parameter of `scrape_tuik` to `False` to skip the Matplotlib preview. Leave it `True` if you want to plot polygons/points before scraping.

---

## Troubleshooting

| Symptom | Suggested fix |
| --- | --- |
| Chrome opens but no data is captured | Ensure the DevTools hook step completed and `window.__my_map` exists (run `!!window.__my_map` in the console). |
| Selenium cannot start Chrome | Confirm Google Chrome is installed and up-to-date. WebDriver Manager downloads a matching driver automatically. |
| Script resumes from the start | Delete or rename the existing CSV, or ensure the file is writable so the dedupe step can read `lon_lat` values. |
| Lots of duplicate rows | Run `tuik_scraper.utils.deduplicate_csv(<path>)` after scraping to clean the file. |

---

## Contributing

Pull requests and issues are welcome. Please describe:
- What region you scraped (so maintainers can reproduce).
- Any manual steps you needed that are not covered here.
- Logs/console output in case of failures.

Happy scraping! 🗺️
