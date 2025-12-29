import argparse
import pandas as pd
import os
from src.data_loader import DataLoader
from src.feature_engineering import FeatureEngineer
from src.model import RaceModel
import sys

def train_mode(args):
    print("Loading data...")
    loader = DataLoader(args.input)
    df = loader.load_data()
    
    print("Feature Engineering...")
    fe = FeatureEngineer()
    df_processed = fe.fit_transform(df)
    
    # Split train/val (Simple split by race_id for time-series/group safety)
    # Here just taking last 20% races as validation
    race_ids = df_processed['race_id'].unique()
    split_idx = int(len(race_ids) * 0.8)
    train_races = race_ids[:split_idx]
    val_races = race_ids[split_idx:]
    
    train_df = df_processed[df_processed['race_id'].isin(train_races)]
    val_df = df_processed[df_processed['race_id'].isin(val_races)]
    
    print(f"Training on {len(train_df)} samples, validating on {len(val_df)} samples...")
    model = RaceModel()
    model.train(train_df, val_df)
    print("Training complete. Model saved.")
    
    print("Evaluating on Validation Set...")
    metrics = model.evaluate(val_df)
    print(f"Validation Metrics: Top-1 Acc: {metrics['top1_accuracy']:.2%}, Top-3 Acc: {metrics['top3_accuracy']:.2%}")

def predict_mode(args):
    print("Loading data for prediction...")
    loader = DataLoader(args.input)
    # If input is None, it generates synthetic data, which is fine for testing
    df = loader.load_data() 
    
    print("Feature Engineering...")
    fe = FeatureEngineer()
    # Note: In a real scenario, we might need to handle cases where 'rank' is not present
    # But FeatureEngineer only transforms features, so it's safe.
    df_processed = fe.transform(df)
    
    print("Predicting...")
    model = RaceModel()
    results = model.predict(df_processed)
    
    # Display top predictions for the first few races
    print("\n--- Prediction Results ---")
    distinct_races = results['race_id'].unique()[:3] # Show first 3 races
    for race_id in distinct_races:
        print(f"Race {race_id} Predictions:")
        race_res = results[results['race_id'] == race_id]
        print(race_res[['horse_id', 'predicted_score']].head(5))

def update_mode(args):
    """
    Appends new data to the main dataset and optionally retrains.
    This assumes we have a 'main' dataset at 'data/raw/races.csv'.
    """
    main_data_path = 'data/raw/races.csv'
    
    if not args.input:
        print("Error: --input is required for update mode (path to new results csv).")
        return

    print(f"Loading new data from {args.input}...")
    # Load new data
    try:
        new_df = pd.read_csv(args.input)
    except FileNotFoundError:
        print(f"File not found: {args.input}")
        return

    # Load existing data or create new
    if os.path.exists(main_data_path):
        print(f"Loading existing data from {main_data_path}...")
        existing_df = pd.read_csv(main_data_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        print("No existing main dataset found. Creating new...")
        combined_df = new_df
        
    # Save combined
    # Ensure dir exists
    os.makedirs(os.path.dirname(main_data_path), exist_ok=True)
    combined_df.to_csv(main_data_path, index=False)
    print(f"Data updated. Total records: {len(combined_df)}")
    print(f"Saved to {main_data_path}")
    
    # Trigger Retraining if requested (implied by requirement "model precision increases")
    print("To retrain the model with new data, run: python main.py --mode train --input data/raw/races.csv")

def main():
    parser = argparse.ArgumentParser(description='Horse Racing Prediction App')
    parser.add_argument('--mode', choices=['train', 'predict', 'update', 'scrape2025'], required=True, help='Mode: train, predict, update, or scrape2025')
    parser.add_argument('--input', type=str, help='Path to input CSV file. If not provided, uses synthetic data.')
    
    args = parser.parse_args()
    
    if args.mode == 'train':
        train_mode(args)
    elif args.mode == 'predict':
        predict_mode(args)
    elif args.mode == 'update':
        update_mode(args)
    elif args.mode == 'scrape2025':
        from src.scraper_2025 import IterativeScraper
        s = IterativeScraper(2023, 2025)
        s.run()

if __name__ == '__main__':
    main()
