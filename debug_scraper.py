import requests
from bs4 import BeautifulSoup
import pandas as pd

def test_scrape(race_id_str):
    url = f"https://db.netkeiba.com/race/{race_id_str}"
    print(f"Testing URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        response.encoding = 'euc-jp'
        html = response.text
        # print(html[:500]) 
        
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", attrs={"summary": "レース結果"})
        if not table:
            print("Table not found")
            return
            
        df = pd.read_html(str(table))[0]
        print("Dataframe head:")
        print(df.head())
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Try a known existing race ID from 2024
    # 202405010101 (Tokyo, 1st Kai, 1st Day, 1st Race)
    test_scrape("202405010101")
