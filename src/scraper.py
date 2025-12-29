import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from tqdm import tqdm
import argparse

import re

def get_race_ids_from_calendar(year):
    """
    Fetches all race IDs for a given year by crawling Netkeiba calendar.
    """
    race_ids = set()
    base_url = "https://race.netkeiba.com/top/calendar.html"
    
    print(f"Collecting race IDs for {year}...")
    for month in range(1, 13):
        url = f"{base_url}?year={year}&month={month}"
        try:
            response = requests.get(url)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find links containing race_id
            links = soup.find_all("a", href=True)
            for link in links:
                href = link['href']
                if "race_id=" in href:
                    match = re.search(r'race_id=(\d+)', href)
                    if match:
                        race_ids.add(match.group(1))
        except Exception as e:
            # print(f"Error fetching calendar for {year}-{month}: {e}")
            pass
        time.sleep(1)
        
    print(f"Found {len(race_ids)} unique races for {year}.")
    # Filter for standard format if needed (12 digits)
    return sorted([rid for rid in race_ids if len(rid) == 12])

def scrape_race(race_id_list):
    """
    Scrapes race results from db.netkeiba.com for the given list of race_ids.
    """
    all_races = []
    base_url = "https://db.netkeiba.com/race/"
    
    print(f"Scraping {len(race_id_list)} races...")
    for race_id in tqdm(race_id_list):
        url = f"{base_url}{race_id}"
        try:
            response = requests.get(url)
            response.encoding = 'euc-jp'
            soup = BeautifulSoup(response.text, "html.parser")
            
            table = soup.find("table", class_="race_table_01")
            if not table:
                continue
                
            intro = soup.find("div", class_="data_intro")
            title = intro.find("h1").text.strip() if intro and intro.find("h1") else str(race_id)
            details = intro.find("p", class_="smalltxt").text.strip() if intro and intro.find("p", class_="smalltxt") else ""
            
            rows = table.find_all("tr")[1:] 
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 10: continue
                
                rank = cols[0].text.strip()
                waku = cols[1].text.strip()
                umaban = cols[2].text.strip()
                horse_name = cols[3].text.strip()
                sex_age = cols[4].text.strip()
                weight = cols[5].text.strip() 
                jockey = cols[6].text.strip()
                time_str = cols[7].text.strip()
                
                # Try to get Horse Weight (usually col 14)
                horse_weight = cols[14].text.strip() if len(cols) > 14 else ""
                trainer = cols[13].text.strip() if len(cols) > 13 else ""

                all_races.append({
                    "race_id": race_id,
                    "race_title": title,
                    "course_len_type": details,
                    "weather_text": details, 
                    "condition_text": details,
                    "着順": rank,
                    "枠番": waku,
                    "馬番": umaban,
                    "馬名": horse_name,
                    "性齢": sex_age,
                    "斤量": weight,
                    "騎手": jockey,
                    "タイム": time_str,
                    "馬体重": horse_weight,
                    "調教師": trainer
                })
                
        except Exception as e:
            continue
        time.sleep(0.1)
        
    return pd.DataFrame(all_races)

def main(start_year, end_year):
    output_dir = "data/raw"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for year in range(start_year, end_year + 1):
        race_ids = get_race_ids_from_calendar(year)
        if not race_ids:
            print(f"No races found for {year}")
            continue
            
        df = scrape_race(race_ids)
        
        if not df.empty:
            output_path = f"{output_dir}/races_real_{year}.csv"
            df.to_csv(output_path, index=False)
            print(f"Saved {len(df)} races to {output_path}")

def scrape_yahoo_race(soup):
    """
    Scrapes race card from Yahoo Sports.
    """
    import re
    race_info = {
        "course_type": "Grass",
        "distance": 1600,
        "weather": "Sunny",
        "condition": "Good",
        "place": "Unknown" 
    }
    
    text = soup.get_text()
    
    # Course Type
    if "芝" in text and "ダ" not in text: race_info["course_type"] = "Grass"
    elif "ダ" in text: race_info["course_type"] = "Dirt" 
    
    # Distance
    dist_match = re.search(r'(\d{3,4})m', text)
    if dist_match:
        race_info["distance"] = int(dist_match.group(1))
        
    # Weather
    if "天候：晴" in text or "天候:晴" in text: race_info["weather"] = "Sunny"
    elif "天候：曇" in text or "天候:曇" in text: race_info["weather"] = "Cloudy"
    elif "天候：雨" in text or "天候:雨" in text: race_info["weather"] = "Rainy"
    elif "天候：雪" in text or "天候:雪" in text: race_info["weather"] = "Rainy"

    # Condition
    if "馬場：良" in text or "馬場:良" in text: race_info["condition"] = "Good"
    elif "馬場：稍" in text or "馬場:稍" in text: race_info["condition"] = "Yielding"
    elif "馬場：重" in text or "馬場:重" in text: race_info["condition"] = "Soft"
    elif "馬場：不" in text or "馬場:不" in text: race_info["condition"] = "Heavy"

    # Horses
    horses = []
    tables = soup.find_all("table")
    target_table = None
    for t in tables:
        if "馬名" in t.get_text():
            target_table = t
            break
            
    if target_table:
        rows = target_table.find_all("tr")
        for row in rows:
            horse_link = row.find("a", href=re.compile(r"/directory/horse/"))
            if not horse_link:
                continue
                
            name = horse_link.get_text().strip()
            
            jockey = "Unknown"
            jockey_link = row.find("a", href=re.compile(r"/directory/jockey/"))
            if jockey_link:
                jockey = jockey_link.get_text().strip()
                
            row_text = row.get_text()
            
            # Waku
            cols = row.find_all("td")
            wakuban = 1
            if cols:
                w_txt = cols[0].get_text().strip()
                if w_txt.isdigit(): wakuban = int(w_txt)
                
            # Sex/Age
            sex = "Male"
            age = 3
            sa_match = re.search(r'([牡牝騸])(\d+)', row_text)
            if sa_match:
                s_char = sa_match.group(1)
                if s_char == '牡': sex = 'Male'
                elif s_char == '牝': sex = 'Female'
                elif s_char == '騸': sex = 'Gelding'
                age = int(sa_match.group(2))
                
            # Horse Weight (BaTaiJu)
            # Pattern: 484(+4) or 484(0) or just 484. Match 3 digits between 300 and 700.
            # Look for 3 digits followed by (
            weight = 470.0 # Default fallback
            
            # Regex for Horse Weight often appears as: 484(+4)
            # Try specific pattern first
            hw_match = re.search(r'(\d{3})\((?:[+-]?\d+|0)\)', row_text)
            if hw_match:
                weight = float(hw_match.group(1))
            else:
                # Fallback: Find any 3 digit number in reasonable range not part of other IDs
                # But be careful of distance usually not in row, but maybe other nums.
                nums = re.findall(r'\b(\d{3})\b', row_text)
                for n in nums:
                    val = float(n)
                    if 350 <= val <= 650:
                        weight = val
                        break
            
            horses.append({
                "wakuban": wakuban,
                "horse_id": name,
                "jockey_id": jockey,
                "age": age,
                "sex": sex,
                "weight": weight
            })
            
    return {"race_info": race_info, "horses": horses}

def scrape_race_card(url):
    """
    Scrapes race card from URL. Supports Netkeiba and Yahoo Sports.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if "netkeiba" in url:
            response.encoding = 'euc-jp'
        else:
            response.encoding = 'utf-8'
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        if "yahoo" in url:
            return scrape_yahoo_race(soup)

        # --- Netkeiba Logic ---
        race_info = {
            "course_type": "Grass",
            "distance": 1600,
            "weather": "Sunny",
            "condition": "Good",
            "place": "Tokyo"
        }
        
        data_intro = soup.find("div", class_="RaceData01")
        if data_intro:
             text = data_intro.text.strip()
             
             if "芝" in text:
                 race_info["course_type"] = "Grass"
             elif "ダ" in text:
                 race_info["course_type"] = "Dirt"
                 
             import re
             dist_match = re.search(r'(\d+)m', text)
             if dist_match:
                 race_info["distance"] = int(dist_match.group(1))
                 
             if "天候:晴" in text: race_info["weather"] = "Sunny"
             elif "天候:曇" in text: race_info["weather"] = "Cloudy"
             elif "天候:雨" in text: race_info["weather"] = "Rainy"
             elif "天候:雪" in text: race_info["weather"] = "Rainy"
             
             if "馬場:良" in text: race_info["condition"] = "Good"
             elif "馬場:稍重" in text: race_info["condition"] = "Yielding"
             elif "馬場:重" in text: race_info["condition"] = "Soft"
             elif "馬場:不良" in text: race_info["condition"] = "Heavy"

        # --- Parse Horses ---
        horses = []
        table = soup.find("table", class_="Shutuba_Table")
        if not table:
             tables = soup.find_all("table")
             for t in tables:
                 if "馬名" in t.text and "騎手" in t.text:
                     table = t
                     break
        
        if table:
            rows = table.find_all("tr", class_="HorseList")
            for row in rows:
                row_text = row.get_text()
                
                # Waku
                # Waku
                cols = row.find_all("td")
                import re
                waku_td = row.find("td", class_=re.compile(r"Waku"))
                if waku_td and waku_td.text.strip().isdigit():
                    wakuban = int(waku_td.text.strip())
                elif cols and cols[0].text.strip().isdigit():
                    # Fallback to first column
                    wakuban = int(cols[0].text.strip())
                else:
                    wakuban = 1
                
                name_span = row.find("span", class_="HorseName")
                name = name_span.text.strip() if name_span else "Unknown"
                
                jockey_td = row.find("td", class_="Jockey")
                jockey = jockey_td.text.strip() if jockey_td else "Unknown"
                jockey = jockey.split('\n')[0].strip()
                
                # Horse Weight
                # Netkeiba: usually labeled "馬体重" in header.
                # In row, look for pattern 3-digit(num)
                weight = 470.0
                
                # Check for explicit 'Weight' class first but verify value
                # Usually class="Weight" is Jockey weight (50-60)
                # But sometimes class="Weight" is used for HorseWeight in other tables?
                # Better to use Regex on row text for 400+ numbers
                
                import re
                hw_match = re.search(r'(\d{3})\((?:[+-]?\d+|0)\)', row_text)
                if hw_match:
                     weight = float(hw_match.group(1))
                else:
                    # Generic find 3 digits
                    nums = re.findall(r'\b(\d{3})\b', row_text)
                    for n in nums:
                        val = float(n)
                        if 340 <= val <= 650:
                            weight = val
                            break

                barei_td = row.find("td", class_="Barei")
                sex = "Male"
                age = 3
                if barei_td:
                    txt = barei_td.text.strip()
                    if "牡" in txt: sex = "Male"
                    elif "牝" in txt: sex = "Female"
                    elif "騸" in txt: sex = "Gelding"
                    
                    age_match = re.search(r'\d+', txt)
                    if age_match:
                        age = int(age_match.group(0))

                horses.append({
                    "wakuban": wakuban,
                    "horse_id": name, 
                    "jockey_id": jockey,
                    "age": age,
                    "sex": sex,
                    "weight": weight
                })
        
        return {"race_info": race_info, "horses": horses}

    except Exception as e:
        print(f"Error scraping url {url}: {e}")
        import traceback
        with open("scraper_debug.log", "w") as f:
            f.write(f"Error scraping {url}: {e}\n")
            traceback.print_exc(file=f)
        return None
