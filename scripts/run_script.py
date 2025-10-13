import sys
import os
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tuik_scraper.scraper import scrape_tuik

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TUİK scraper for a specific il (province).")
    parser.add_argument("--il", type=str, nargs="+", required=True, help="Name of the province (e.g., Yalova)")
    #parser.add_argument("-tr",type=str,required=False, help="Scrape the whole country")

    args = parser.parse_args()

    print(f"🚀 Starting TUİK scraper for {args.il}...")
    scrape_tuik(il=args.il)
    print("✅ Done.")
