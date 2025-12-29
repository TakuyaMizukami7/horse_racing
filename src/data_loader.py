import pandas as pd
import numpy as np
from typing import List, Optional

class DataLoader:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path

    def load_data(self) -> pd.DataFrame:
        """Loads data from CSV if path is provided, else generates synthetic data."""
        if self.data_path:
            df = pd.read_csv(self.data_path)
            # Check if it's real data by checking for Japanese columns
            if '着順' in df.columns:
                return self.preprocess_real_data(df)
            return df
        else:
            return self.generate_synthetic_data()

    def preprocess_real_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocesses real scraped data to match model expected schema."""
        # Filter out invalid ranks (non-numeric like 取, 除, 中)
        df = df[pd.to_numeric(df['着順'], errors='coerce').notnull()].copy()
        df['rank'] = df['着順'].astype(int)
        
        # Renaissance Map & Parsing
        
        # Sex and Age from "性齢" (e.g., "牡3" -> Sex="Male", Age=3)
        # Map Japanese Sex to English expected by model (Male, Female, Gelding)
        sex_map = {'牡': 'Male', '牝': 'Female', 'セ': 'Gelding'}
        
        def parse_sex_age(val):
            val = str(val)
            sex_char = val[0]
            age_str = val[1:]
            return sex_map.get(sex_char, 'Male'), int(age_str) if age_str.isdigit() else 3
            
        df[['sex', 'age']] = df['性齢'].apply(lambda x: pd.Series(parse_sex_age(x)))
        
        # Horse Weight from "馬体重" (e.g., "466(-12)" -> 466)
        def parse_weight(val):
            val = str(val)
            # Take part before '('
            if '(' in val:
                return float(val.split('(')[0])
            try:
                return float(val)
            except:
                return 470.0 # Default fallback
        
        df['weight'] = df['馬体重'].apply(parse_weight)
        
        # Parse Course Info from "course_len_type" (e.g., "ダ右1200m")
        def parse_course(val):
            val = str(val)
            course_type = 'Dirt' if 'ダ' in val else 'Grass'
            # Extract digits matches
            import re
            dist_match = re.search(r'\d+', val)
            distance = int(dist_match.group()) if dist_match else 1600
            return course_type, distance

        if 'course_len_type' in df.columns and df['course_len_type'].notna().all():
             df[['course_type', 'distance']] = df['course_len_type'].apply(lambda x: pd.Series(parse_course(x)))
        else:
             # Fallbacks if columns missing or NaN
             df['course_type'] = 'Grass'
             df['distance'] = 1600
             
        # Parse Weather from "weather_text" (e.g., "天候 : 晴")
        # Map to "Sunny", "Cloudy", "Rainy" (Model was trained on synthetic distinct values)?
        # Real data: 晴, 曇, 雨, 小雨, 雪, etc.
        # Synthetic: Sunny, Cloudy, Rainy
        weather_map = {'晴': 'Sunny', '曇': 'Cloudy', '雨': 'Rainy', '小雨': 'Rainy', '雪': 'Rainy'}
        def parse_weather(val):
            if not isinstance(val, str): return 'Cloudy'
            # val might be "天候 : 晴"
            if ':' in val:
                val = val.split(':')[1].strip()
            return weather_map.get(val, 'Cloudy')

        if 'weather_text' in df.columns:
            df['weather'] = df['weather_text'].apply(parse_weather)
        else:
            df['weather'] = 'Cloudy'
            
        # Parse Condition from "condition_text" (e.g., "ダート : 良")
        # Synthetic: Good, Yielding, Soft, Heavy
        # Real: 良, 稍重, 重, 不良
        cond_map = {'良': 'Good', '稍重': 'Yielding', '重': 'Soft', '不良': 'Heavy'}
        def parse_condition(val):
            if not isinstance(val, str): return 'Good'
            if ':' in val:
                val = val.split(':')[1].strip()
            return cond_map.get(val, 'Good')
            
        if 'condition_text' in df.columns:
            df['track_condition'] = df['condition_text'].apply(parse_condition)
        else:
            df['track_condition'] = 'Good'
            
        # Parse Race Time "タイム" (e.g. "1:34.5") -> Seconds
        def parse_time(val):
            val = str(val)
            if not val or val == 'nan': return None
            try:
                parts = val.split(':')
                if len(parts) == 2:
                    return float(parts[0]) * 60 + float(parts[1])
                return float(val)
            except:
                return None
        
        if 'タイム' in df.columns:
            df['race_time'] = df['タイム'].apply(parse_time)
        else:
            df['race_time'] = None

        # Rename/Map other columns
        df['horse_id'] = df['馬名'] # Use Name as ID
        df['jockey_id'] = df['騎手'] # Will be LabelEncoded
        df['trainer_id'] = df['調教師'] # Will be LabelEncoded
        df['wakuban'] = df['枠番']
        
        # Ensure we return relevant columns
        cols = ['race_id', 'horse_id', 'distance', 'course_type', 'weather', 'track_condition', 
                'age', 'sex', 'weight', 'jockey_id', 'trainer_id', 'wakuban', 'rank', 'race_time']
        
        # Filter mostly to be safe
        return df[cols]

if __name__ == "__main__":
    loader = DataLoader()
    df = loader.load_data()
    print(df.head())
