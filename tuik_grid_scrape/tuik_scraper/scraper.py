import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from .utils import save_to_csv
from selenium.webdriver.common.by import By

from .js_injections import MAP_HOOK, HOVER_LISTENER, CHROMEDRIVER_PATH

def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options) # Define the driver
    return driver

def hook_map(driver):
    driver.get("https://cip.tuik.gov.tr/") # Open the desired website
    time.sleep(5)
    driver.execute_script(MAP_HOOK) # execute map hook script on console
    print("✅ Hook injection sent.")
    print("Add breakpoint to var t = i.map.queryRenderedFeatures(e.point, {layers: ['grid_katmani']")
    print("Then run window.__my_map = i.map; command on console")
    input("👉 Please open DevTools > Console and confirm map is hooked (you should see '✅ Hooked map instance'). Then press Enter to continue...")

    exists = driver.execute_script("return typeof window.__my_map !== 'undefined';")
    if not exists:
        raise RuntimeError("❌ Map object was not hooked. Please make sure the hook worked.")
    print("✅ Map object available.")
    click_to_button(driver,button="btn-nuts-grid")
    zoom_to_area(driver,distance=10)

def click_to_button(driver,button):
    button = driver.find_element(By.ID, button)
    button.click()

def zoom_to_area(driver,lon=28.97,lat=41.01,distance=9):
    driver.execute_script(f'window.__my_map.jumpTo({{ center: [{lon}, {lat}], zoom: {distance} }});')
    print('Zoomed in')

def start_hover_capture(driver, duration=30):
    driver.execute_script(HOVER_LISTENER)
    zoom_to_area(driver,lon=39.2986305,lat=44.4216184,distance = 9)
    print("🟢 Hover listener injected. Hover over the map...")
    time.sleep(duration)
    while True:
        continue_hovering = input("Do you want to continue hovering? (yes/no)").strip().lower()
        if continue_hovering =='yes':
            duration +=30
            time.sleep(duration)
        elif continue_hovering =='no':
            zoom_to_area(driver,39.941791163745386,32.75899890208769,distance=2)
            zoom_to_area(driver,39.950396336476224,32.7621631758702,distance=2)
            zoom_to_area(driver, 39.95629988067327,32.77659419321532,distance=2)
            zoom_to_area(driver, 39.96488521932998,32.77976992871405,distance=2)
            break
        else:
            print('Wrong input')
            continue
    
    return driver.execute_script("return window.__hoveredFeatures || [];")

def scrape_tuik(duration=60, output_path="//Users/borangoksel/Documents/GitHub/tuik_grid_scraper/tuik_grid_scrape/data/tuik_hover_data.csv"):
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
