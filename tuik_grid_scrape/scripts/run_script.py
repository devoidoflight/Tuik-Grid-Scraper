import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tuik_scraper.scraper import scrape_tuik
if __name__ == "__main__":
    print("🚀 Starting TUİK scraper...")  # Add this debug print
    scrape_tuik(duration=60)
    print("✅ Done.")