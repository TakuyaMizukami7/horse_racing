import pandas as pd
import os
import glob

def merge_csvs():
    # List of files to merge
    files = [
        'data/raw/races_all_2020_2023.csv',
        'data/raw/races_real_2024.csv'
    ]
    
    dfs = []
    for f in files:
        if os.path.exists(f):
            print(f"Loading {f}...")
            try:
                df = pd.read_csv(f)
                dfs.append(df)
            except Exception as e:
                print(f"Error loading {f}: {e}")
        else:
            print(f"Warning: {f} not found.")
            
    if not dfs:
        print("No data to merge.")
        return

    # Concatenate
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Validation/Cleaning (Simple)
    # Ensure race_id is string
    if 'race_id' in merged_df.columns:
        merged_df['race_id'] = merged_df['race_id'].astype(str)
        
    output_path = 'data/raw/races_merged_2020_2024.csv'
    merged_df.to_csv(output_path, index=False)
    print(f"Merged data saved to {output_path}. Total rows: {len(merged_df)}")

if __name__ == "__main__":
    merge_csvs()
