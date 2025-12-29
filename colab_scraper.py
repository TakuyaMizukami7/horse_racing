# Google Colab Scraper Script for Netkeiba (2023-2025)
# Instructions:
# 1. Create a new Notebook in Google Colab.
# 2. Copy and paste this entire script into a code cell.
# 3. Run the cell.
# 4. Process will start gathering data.
# 5. When finished, check the 'data/raw' folder in the left sidebar and download the CSV files.

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
from datetime import datetime

class IterativeScraper:
    def __init__(self, start_year=2023, end_year=2025):
        self.base_url = "https://race.netkeiba.com/race/result.html"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.start_year = start_year
        self.end_year = end_year
        self.start_time = time.time()
        self.last_report_time = time.time()
        self.total_races_scraped = 0
        self.current_year_data = [] # Data for the current year being scraped
        self.existing_ids = set()

    def load_existing_for_year(self, year):
        self.existing_ids = set()
        out_path = f"data/raw/races_real_{year}.csv"
        if os.path.exists(out_path):
            try:
                # Check for empty file
                if os.path.getsize(out_path) == 0:
                     return
                df = pd.read_csv(out_path)
                if 'race_id' in df.columns:
                    self.existing_ids = set(df['race_id'].astype(str))
                    print(f"Loaded {len(self.existing_ids)} existing races for {year}. Will skip these.", flush=True)
            except Exception as e:
                print(f"Warning: Could not load existing data for {year}: {e}", flush=True)

    def save_data(self, year):
        if self.current_year_data:
            df = pd.DataFrame(self.current_year_data)
            out_dir = "data/raw"
            os.makedirs(out_dir, exist_ok=True)
            out_path = f"data/raw/races_real_{year}.csv"
            
            # Check existence before saving to decide mode/header
            exists = os.path.exists(out_path) and os.path.getsize(out_path) > 0
            mode = 'a' if exists else 'w'
            header = not exists
            
            df.to_csv(out_path, mode=mode, header=header, index=False)
            print(f"\n[AUTO-SAVE] Appended {len(df)} rows to {out_path} (Mode: {mode})", flush=True)
            
            # Clear memory after save
            self.current_year_data = [] 

    def check_status(self):
        """Prints status update every 5 minutes."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        since_last_report = current_time - self.last_report_time
        
        if since_last_report >= 300:  # 5 minutes
            minutes = elapsed / 60
            print(f"[STATUS] Running for {minutes:.1f} minutes. Found {self.total_races_scraped} NEW races total.", flush=True)
            self.last_report_time = current_time

    def fetch_race(self, race_id):
        url = f"{self.base_url}?race_id={race_id}"
        try:
            time.sleep(1) # Polite delay
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # Handling encoding
            response.encoding = response.apparent_encoding 
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check if race exists and has results
            table = soup.find("table", id="All_Result_Table")
            if not table:
                return None
            
            # Basic Info
            intro = soup.find("div", class_="RaceName")
            race_title = intro.text.strip() if intro else str(race_id)
            
            data_intro = soup.find("div", class_="RaceData01")
            race_details = data_intro.text.strip() if data_intro else ""
            
            # Parse Rows
            rows = table.find_all("tr", class_="HorseList")
            
            race_results = []
            for row in rows:
                rank_div = row.find("div", class_="Rank")
                rank = rank_div.text.strip() if rank_div else ""
                if not rank.isdigit(): continue 
                
                waku_td = row.find("td", class_="Waku")
                waku = waku_td.text.strip() if waku_td else ""
                
                umaban_td = row.find("td", class_="Num")
                umaban = umaban_td.text.strip() if umaban_td else ""
                
                horse_name_span = row.find("span", class_="Horse_Name")
                horse_name = horse_name_span.text.strip() if horse_name_span else ""
                
                jockey_td = row.find("td", class_="Jockey")
                jockey = jockey_td.text.strip() if jockey_td else ""
                
                time_span = row.find("span", class_="RaceTime")
                race_time = time_span.text.strip() if time_span else ""
                
                weight_td = row.find("td", class_="Weight")
                weight = weight_td.text.strip() if weight_td else ""
                
                trainer_td = row.find("td", class_="Trainer")
                trainer = trainer_td.text.strip() if trainer_td else ""

                race_results.append({
                    "race_id": race_id,
                    "race_title": race_title,
                    "course_len_type": race_details,
                    "weather_text": race_details,
                    "condition_text": race_details,
                    "着順": rank,
                    "枠番": waku,
                    "馬番": umaban,
                    "馬名": horse_name,
                    "騎手": jockey,
                    "タイム": race_time,
                    "斤量": weight,
                    "調教師": trainer,
                    "性齢": "", 
                    "馬体重": "" 
                })
                
            return race_results

        except Exception as e:
            return None

    def run(self):
        print(f"Starting Iterative Scrape for years: {self.start_year} to {self.end_year}", flush=True)
        
        venues = range(1, 11) 
        kais = range(1, 7) 
        days = range(1, 13) 
        races = range(1, 13) 
        
        for year in range(self.start_year, self.end_year + 1):
            print(f"--- Processing Year {year} ---", flush=True)
            self.load_existing_for_year(year)
            self.current_year_data = [] # Reset for new year
            
            consecutive_failures = 0
            
            for venue in venues:
                venue_str = f"{venue:02}"
                print(f"Checking Venue {venue_str} ({year})...", flush=True)
                for kai in kais:
                    kai_str = f"{kai:02}"
                    for day in days:
                        day_str = f"{day:02}"
                        
                        found_race_in_day = False
                        
                        for race in races:
                            race_str = f"{race:02}"
                            race_id = f"{year}{venue_str}{kai_str}{day_str}{race_str}"
                            
                            # Optimization: Skip if already exists
                            if race_id in self.existing_ids:
                                 found_race_in_day = True 
                                 continue
    
                            self.check_status()
                            
                            results = self.fetch_race(race_id)
                            if results:
                                self.current_year_data.extend(results)
                                self.total_races_scraped += 1
                                print(f"\rFound Race: {race_id} ({len(results)} rows)", flush=True)
    
                                # Auto-save every 50 races
                                if len(self.current_year_data) >= 500: 
                                    self.save_data(year)
    
                                found_race_in_day = True
                                consecutive_failures = 0
                            else:
                                if race == 1:
                                    break 
                        
                        if not found_race_in_day:
                            consecutive_failures += 1
                        
                        if consecutive_failures > 100: 
                             pass
            
            # Final save for the year
            if self.current_year_data:
                self.save_data(year)
                
        print(f"\nFinished. Total races scraped: {self.total_races_scraped}", flush=True)

if __name__ == "__main__":
    # Ensure data directory exists
    if not os.path.exists('data/raw'):
        os.makedirs('data/raw')
        
    scraper = IterativeScraper(2023, 2025)
    scraper.run()
