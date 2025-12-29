import optuna
import pandas as pd
import lightgbm as lgb
import os
import pickle
from src.data_loader import DataLoader
from src.feature_engineering import FeatureEngineer
from sklearn.metrics import mean_squared_error
import numpy as np

def objective(trial):
    # Load Data (Memoize if possible, but for simplicity load once globally if large)
    # Inside objective standard practice is fast, but here data loading is slow.
    # We will load data outside.
    pass

if __name__ == "__main__":
    print("Loading data for tuning...")
    input_path = "data/raw/races_cleaned.csv"
    loader = DataLoader(input_path)
    df = loader.load_data()
    
    print("Feature Engineering...")
    fe = FeatureEngineer()
    df_processed = fe.fit_transform(df)
    
    # Split
    race_ids = df_processed['race_id'].unique()
    split_idx = int(len(race_ids) * 0.8)
    train_races = race_ids[:split_idx]
    val_races = race_ids[split_idx:]
    
    train_df = df_processed[df_processed['race_id'].isin(train_races)]
    val_df = df_processed[df_processed['race_id'].isin(val_races)]
    
    # Features
    feature_cols = [
        'distance', 'course_type', 'weather', 'track_condition',
        'age', 'sex', 'weight', 'jockey_id', 'trainer_id', 'wakuban', 
        'prev_rank', 'prev_speed_index'
    ]
    
    X_train = train_df[feature_cols]
    y_train = train_df['rank']
    X_val = val_df[feature_cols]
    y_val = val_df['rank']
    
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val)
    
    def objective(trial):
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'verbosity': -1,
            'boosting_type': 'gbdt',
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'num_leaves': trial.suggest_int('num_leaves', 20, 150),
            'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0),
            'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0),
            'bagging_freq': trial.suggest_int('bagging_freq', 1, 7),
            'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
            'feature_pre_filter': False
        }
        
        callback = lgb.early_stopping(stopping_rounds=10, verbose=False)
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=300,
            valid_sets=[val_data],
            callbacks=[callback]
        )
        
        # Predict constraints or post-processing?
        preds = model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        return rmse

    print("Starting optimization...")
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=50)
    
    print("\nBest params:")
    print(study.best_params)
    
    # Retrain final model
    print("Retraining final model with best params...")
    best_params = study.best_params
    best_params['objective'] = 'regression'
    best_params['metric'] = 'rmse'
    best_params['boosting_type'] = 'gbdt'
    
    # Train heavily
    final_model = lgb.train(
        best_params,
        train_data,
        num_boost_round=500,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=20)]
    )
    
    # Save Model (LightGBM Native)
    model_dir = 'data/processed'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    final_model.save_model(os.path.join(model_dir, 'lgbm_model.txt'))
    print("Tuned model saved.")
    
    # Evaluate Top-3 Accuracy on Val
    preds = final_model.predict(X_val)
    val_df_res = val_df.copy()
    val_df_res['predicted_score'] = preds
    
    top3_hits = 0
    total_races = 0
    
    for race_id, group in val_df_res.groupby('race_id'):
        true_winner = group[group['rank'] == 1]
        if true_winner.empty: continue
        total_races += 1
        true_id = true_winner.iloc[0]['horse_id']
        
        sorted_group = group.sort_values('predicted_score')
        top3 = sorted_group.iloc[:3]['horse_id'].values
        if true_id in top3:
            top3_hits += 1
            
    print(f"Final Validation Top-3 Accuracy: {top3_hits/total_races:.2%}")
