import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from src.scraper import main

if __name__ == "__main__":
    print("Starting scrape for 2025...")
    main(2025, 2025)
    print("Finished scrape for 2025.")
