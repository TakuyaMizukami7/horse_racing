from src.scraper import scrape_race_card
import sys

# Example URL (using a past race, structure should be similar for Shutuba if table exists)
# Note: Shutuba table might be empty if race is long past, but let's see if it errors out globally.
# Or I can try a dummy URL that will fail network to check error handling, but I want to check parsing logic.
# Let's try to pass a URL that likely works or at least parses.
# Netkeiba Shutuba URLs look like: https://race.netkeiba.com/race/shutuba.html?race_id=202305050811
url = "https://race.netkeiba.com/race/shutuba.html?race_id=202409050801" # Random valid-ish ID

print(f"Testing scraper with {url}")
try:
    data = scrape_race_card(url)
    if data:
        print("Success!")
        print(f"Horses found: {len(data['horses'])}")
        if data['horses']:
            print(f"Sample Horse: {data['horses'][0]}")
    else:
        print("Returned None")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
