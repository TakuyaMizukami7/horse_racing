import pandas as pd
import os
import sys

def clean_data():
    files = [
        "data/raw/races_real_2023_max.csv",
        "data/raw/races_real_2024_max.csv",
        "data/raw/races_real_2025.csv"
    ]
    
    dfs = []
    print("Loading and cleaning files...")
    for f in files:
        if os.path.exists(f):
            print(f"Processing {f}...")
            # Use 'on_bad_lines' to skip corrupted rows if any
            try:
                df = pd.read_csv(f, on_bad_lines='skip')
                
                # Fix: "斤量" has Horse Weight, move to "馬体重"
                # Check if "斤量" has large values (mean > 100)
                # Convert to numeric first
                kinryo = pd.to_numeric(df['斤量'], errors='coerce')
                
                if kinryo.mean() > 100:
                    print(f"  Detected Horse Weight in '斤量' column (Mean: {kinryo.mean():.1f}). Moving to '馬体重'.")
                    df['馬体重'] = df['斤量']
                    # Optional: Set 斤量 to default 55.0 since it's missing (Jockey Weight)
                    df['斤量'] = 55.0
                
                dfs.append(df)
            except Exception as e:
                print(f"Error reading {f}: {e}")
        else:
            print(f"Warning: File {f} not found.")
            
    if not dfs:
        print("No data found.")
        return

    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Sex/Age handling: DataLoader defaults invalid entries to Male/3, so NaNs are fine.
    
    output_path = "data/raw/races_cleaned.csv"
    combined_df.to_csv(output_path, index=False)
    print(f"Saved cleaned data to {output_path} (Rows: {len(combined_df)})")
    
    return output_path

if __name__ == "__main__":
    cleaned_path = clean_data()
    
    if cleaned_path:
        print("\n--- Starting Training ---")
        # Call main.py train logic
        # Using run_command to keep it clean or import
        os.system(f"python main.py --mode train --input {cleaned_path}")
