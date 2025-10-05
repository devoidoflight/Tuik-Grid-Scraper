import time
import datetime
import pandas as pd
import subprocess
import pyautogui  
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from .utils import save_to_csv
from selenium.webdriver.common.by import By
from pathlib import Path


from .js_injections import MAP_HOOK, CAPTURE_VISIBLE_GRID, CHROMEDRIVER_PATH
from .coordinate_generator import load_geojson, extract_polygons, generate_grid

BASE_DIR = Path.cwd().resolve()


def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(f'{BASE_DIR}/resources/chromedriver-mac-arm64/chromedriver'), options=options)
    
    # Ensure the browser is front and visible
    driver.set_window_position(0, 0)
    driver.set_window_size(1400, 1000)
    return driver


def hook_map(driver):
    driver.get("https://cip.tuik.gov.tr/") # Open the desired website
    time.sleep(5)
    driver.execute_script(MAP_HOOK) # execute map hook script on console
    print("✅ Hook injection sent.")
    print(BASE_DIR)
    print("Add breakpoint to var t = i.map.queryRenderedFeatures(e.point, {layers: ['grid_katmani']")
    print("Then run window.__my_map = i.map; command on console")
    input("👉 Please open DevTools > Console and confirm map is hooked (you should see '✅ Hooked map instance'). Then press Enter to continue...")

    exists = driver.execute_script("return typeof window.__my_map !== 'undefined';")
    if not exists:
        raise RuntimeError("❌ Map object was not hooked. Please make sure the hook worked.")
    print("✅ Map object available.")
    click_to_button(driver,button="btn-nuts-grid")

def click_to_button(driver,button):
    button = driver.find_element(By.ID, button)
    button.click()


def zoom_to_area(driver, lon, lat, distance=9):
    # 1. Bring Chrome to front (macOS only)
    subprocess.run([
        "osascript", "-e",
        'tell application "Google Chrome" to activate'
    ])

    time.sleep(0.05)  # Let browser come forward

    # 2. Zoom map
    driver.execute_script(f'window.__my_map.jumpTo({{ center: [{lon}, {lat}], zoom: {distance} }});')
    time.sleep(0.05)

    # 3. Force paint
    driver.execute_script("window.scrollTo(0, 0);")

    # 4. Click to center of screen to trigger focus/render
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(screen_width // 2, screen_height // 2)

    print(f'🔍 Zoomed to [{lon}, {lat}] at zoom level {distance}')


def start_grid_capture(driver, coords, zoom=9, delay=3):
   
    print("🟢 Grid capture starting.")

    all_data = []
    seen_ids = set()

    for i, (lon, lat) in enumerate(coords):
    
        print(f"📍 Moving to square {i+1}/{len(coords)}: ({lon}, {lat})")
        print(f'Current time is: {datetime.datetime.now()}')
        zoom_to_area(driver, lon=lon, lat=lat, distance=zoom)
        time.sleep(delay)
        driver.execute_script(CAPTURE_VISIBLE_GRID)
        data = driver.execute_script("return window.__visibleGrids || [];")
        new_data = [
    {**item, 'lon': lon, 'lat': lat}
    for item in data
    if item['id'] not in seen_ids
]
        all_data.extend(new_data)

        # Prevent duplicates
        for item in new_data:
            seen_ids.add(item["id"])

        print(f"✅ Captured {len(new_data)} new grids (Total: {len(all_data)})")

    return all_data


def scrape_tuik(il, output_path=f"{BASE_DIR}/data/tuik_grid_data_tr.csv"):
    driver = init_driver()
    try:
        hook_map(driver)

        # Load GeoJSON and process data
        if il[0] == 'Türkiye':
            features = load_geojson(f'{BASE_DIR}/resources/turkey-admin-level-2.geojson', il[0])
        else:
            features = []
            for i in il:
                features.extend(load_geojson(f'{BASE_DIR}/resources/turkey-admin-level-4.geojson', i))
        polygons = extract_polygons(features)
        red_points = [generate_grid(polygons, 3000)]  # Unpack both

        for coords in red_points:
            data = start_grid_capture(driver,coords=coords,zoom=11, delay=0
                                      )

            if data:
                print(f"📦 Saved {len(data)} grid squares.")
                save_to_csv(data, output_path)
            else:
                print("⚠️ No data captured.")

    finally:
        driver.quit()


