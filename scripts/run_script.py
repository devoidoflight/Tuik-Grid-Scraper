import sys
import os
import argparse
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tuik_scraper.scraper import scrape_tuik

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TUİK scraper for a specific il (province).")
    parser.add_argument("--il", type=str, nargs="+", required=True, help="Name of the province (e.g., Yalova)")
    parser.add_argument("--yyyy", type=int, nargs="?", required=False, help="Year of the statistics",default=(date.today().year)-1)
    #parser.add_argument("-tr",type=str,required=False, help="Scrape the whole country")

    args = parser.parse_args()

    # Exit if the year is invalid
    if args.yyyy>(date.today().year)-1:
        print(f"Latest data collection year is {(date.today().year)-1}. Enter a year between 2022 and {(date.today().year)-1}")
        sys.exit(1)

    print(f"🚀 Starting TUİK scraper for {args.il} in {args.yyyy}...")
    scrape_tuik(il=args.il,year = args.yyyy)
    print("✅ Done.")
