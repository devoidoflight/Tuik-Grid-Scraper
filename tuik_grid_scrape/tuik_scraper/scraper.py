import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from .js_injections import MAP_HOOK, HOVER_LISTENER
from .utils import save_to_csv

def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def hook_map(driver):
    driver.get("https://cip.tuik.gov.tr/")
    time.sleep(5)
    driver.execute_script(MAP_HOOK)
    print("✅ Hook injection sent.")

    input("👉 Please open DevTools > Console and confirm map is hooked (you should see '✅ Hooked map instance'). Then press Enter to continue...")

    exists = driver.execute_script("return typeof window.__my_map !== 'undefined';")
    if not exists:
        raise RuntimeError("❌ Map object was not hooked. Please make sure the hook worked.")
    print("✅ Map object available.")

def start_hover_capture(driver, duration=60):
    driver.execute_script(HOVER_LISTENER)
    print("🟢 Hover listener injected. Hover over the map...")
    time.sleep(duration)
    return driver.execute_script("return window.__hoveredFeatures || [];")

def scrape_tuik(duration=60, output_path="/Users/borangoksel/Documents/GitHub/Çöplük/tuik_grid_scrape/data/tuik_hover_data.csv"):
    driver = init_driver()
    try:
        hook_map(driver)
        data = start_hover_capture(driver, duration=duration)
    finally:
        driver.quit()

    if data:
        print(f"✅ Retrieved {len(data)} items.")
        save_to_csv(data, output_path)
    else:
        print("⚠️ No data collected.")
