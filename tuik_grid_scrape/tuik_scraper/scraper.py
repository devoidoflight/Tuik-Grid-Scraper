import time
import datetime
import pandas as pd
import subprocess, platform
import pyautogui  
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from .utils import save_to_csv,visualize_scraped_points
from selenium.webdriver.common.by import By
from pathlib import Path


from .js_injections import MAP_HOOK, CAPTURE_VISIBLE_GRID, CHROMEDRIVER_PATH
from .coordinate_generator import load_geojson, extract_polygons, generate_grid

BASE_DIR = Path.cwd().resolve()


def init_driver():
    options = Options()
    options.add_argument("--start-maximized")  # visible, not headless

    # ✅ Let Selenium auto-resolve the correct ChromeDriver for the OS/Chrome
    driver = webdriver.Chrome(options=options)

    # Keep your positioning if you want a fixed window size/position
    try:
        driver.set_window_position(0, 0)
        driver.set_window_size(1400, 1000)
    except Exception:
        # Some platforms ignore manual sizing after start-maximized; safe to skip
        pass

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
    # 1) Bring Chrome to front (macOS only). Skip on Windows/Linux.
    if platform.system() == "Darwin":
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "Google Chrome" to activate'],
                check=False
            )
            time.sleep(0.05)  # Let browser come forward
        except FileNotFoundError:
            # osascript not found (e.g., headless mac or no AppleScript); ignore
            pass
    else:
        # Cross-platform, Selenium-only focus (safe fallback)
        try:
            driver.switch_to.window(driver.current_window_handle)
            driver.maximize_window()
        except Exception:
            pass

    # 2) Zoom map
    driver.execute_script(
        f'window.__my_map.jumpTo({{ center: [{lon}, {lat}], zoom: {distance} }});'
    )
    time.sleep(0.05)

    # 3) Force paint/focus via JS (works on all OSes; avoids OS-level clicks)
    driver.execute_script("""
        if (window.__my_map) {
            try { window.__my_map.resize(); } catch(e) {}
            try { window.__my_map.triggerRepaint && window.__my_map.triggerRepaint(); } catch(e) {}
            try {
                const c = window.__my_map.getCanvas && window.__my_map.getCanvas();
                if (c && c.focus) c.focus();
            } catch(e) {}
        }
        window.scrollTo(0, 0);
    """)

    # (Optional) If you still want a physical click on macOS only:
    # if platform.system() == "Darwin":
    #     import pyautogui
    #     sw, sh = pyautogui.size()
    #     pyautogui.click(sw // 2, sh // 2)

    print(f'🔍 Zoomed to [{lon}, {lat}] at zoom level {distance}')


def start_grid_capture(driver, coords, zoom=9, delay=3):
   
    print("🟢 Grid capture starting.")

    all_data = []
    seen_ids = set()
    
    try:
        for i, (lon, lat) in enumerate(coords):
        
            print(f"📍 Moving to square {i+1}/{len(coords)}: ({lon}, {lat})")
            print(f'Current time is: {datetime.datetime.now()}')
            zoom_to_area(driver, lon=lon, lat=lat, distance=zoom)
            time.sleep(delay)
            driver.execute_script(CAPTURE_VISIBLE_GRID)
            data = driver.execute_script("return window.__visibleGrids || [];")
            new_data = [{**item, 'lon': lon, 'lat': lat} for item in data]
            all_data.extend(new_data)


            print(f"✅ Captured {len(new_data)} grids (Total: {len(all_data)})")
    except Exception:
        print("Chrome crashed")
        

    finally:
        return all_data


def scrape_tuik(il, output_path=f"{BASE_DIR}/data/tuik_grid_data_tr_30.csv",visualize_points = True):
    driver = init_driver()
    try:
        hook_map(driver)

        # Normalize to Path and ensure folder exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load GeoJSON and process data
        if il[0] == 'Türkiye':
            features = load_geojson(f'{BASE_DIR}/resources/turkey-admin-level-2.geojson', il[0])
        else:
            features = []
            for city in il:
                features.extend(load_geojson(f'{BASE_DIR}/resources/turkey-admin-level-4.geojson', city))
        polygons = extract_polygons(features)
        red_points = [generate_grid(polygons, 30000)]  # list[list[(lon, lat)]]
        visualize_scraped_points(polygons,red_points)



        # ---- resume logic (ONLY if the CSV already exists) ----
        if output_path.exists():
            existing_data = pd.read_csv(output_path,usecols=['lon_lat']) 
            existing_data = existing_data["lon_lat"].to_list()
            existing_data = set(existing_data)
            existing_data = list(existing_data)

            for i in range(len(existing_data)):
                existing_data[i] = existing_data[i].replace('(', '').replace(')', '').replace('POINT','').replace(' ',',').split(',')

            tupled_data = []
            for i in existing_data:
                try:
                    tupled_data.append((np.float64(i[0]),np.float64(i[1])) )
                except ValueError:
                    print(f'Error value:{i}')
            len1 = len(red_points[0])
            red_points = [[item for item in red_points[0] if item not in tupled_data]]
            print(f'rp: {len1}, frp: {len(red_points[0])}')
        

        for coords in red_points:
            data = start_grid_capture(driver, coords=coords, zoom=10.5, delay=0)
            if data:
                print(f"📦 Saved {len(data)} grid squares.")
                save_to_csv(data, output_path)  # accepts Path or str
            else:
                print("⚠️ No data captured.")
    finally:
        driver.quit()


