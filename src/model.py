import lightgbm as lgb
import pandas as pd
import os
import pickle
from typing import Dict, Any

class RaceModel:
    def __init__(self, model_dir: str = 'data/processed'):
        self.model_dir = model_dir
        self.model = None
        self.feature_cols = [
            'distance', 'course_type', 'weather', 'track_condition',
            'age', 'sex', 'weight', 'jockey_id', 'trainer_id', 'wakuban', 'prev_rank', 'prev_speed_index'
        ]
        
    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None):
        """Trains the LightGBM model."""
        X_train = train_df[self.feature_cols]
        # Target: 1 if rank <= 3 (Top 3), else 0. Simple Binary Classification for now.
        # Or Regression on Rank? Let's do Regression on log(rank) or just Rank.
        y_train = train_df['rank']
        
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9
        }
        
        train_data = lgb.Dataset(X_train, label=y_train)
        valid_sets = [train_data]
        
        if val_df is not None:
            X_val = val_df[self.feature_cols]
            y_val = val_df['rank']
            val_data = lgb.Dataset(X_val, label=y_val)
            valid_sets.append(val_data)
        
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=valid_sets,
            callbacks=[lgb.early_stopping(stopping_rounds=10)]
        )
        
        self.save_model()

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predicts ranks/scores for the input dataframe."""
        if self.model is None:
            self.load_model()
            
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        df_out = df.copy()
        df_out['predicted_score'] = preds
        # Sort by predicted score (lower rank is better for regression)
        df_out = df_out.sort_values('predicted_score')
        return df_out

    def save_model(self):
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        # Use LightGBM native save
        self.model.save_model(os.path.join(self.model_dir, 'lgbm_model.txt'))

    def load_model(self):
        model_path = os.path.join(self.model_dir, 'lgbm_model.txt')
        self.model = lgb.Booster(model_file=model_path)

    def evaluate(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculates Top-1 and Top-3 accuracy."""
        if self.model is None:
            self.load_model()
            
        predictions = self.predict(df)
        
        # Calculate accuracy per race
        top1_hits = 0
        top3_hits = 0
        total_races = 0
        
        for race_id, group in predictions.groupby('race_id'):
            # True winner (rank 1)
            true_winner = group[group['rank'] == 1]
            if true_winner.empty:
                continue
                
            total_races += 1
            true_winner_id = true_winner.iloc[0]['horse_id']
            
            # Predicted ranking (already sorted by predicted_score in predict method)
            # predict returns sorted group? No, predict returns full df, we need to sort here if not ensuring order
            # The predict method returns sorted df but let's be safe
            sorted_group = group.sort_values('predicted_score')
            
            # Top 1 Prediction
            pred_winner_id = sorted_group.iloc[0]['horse_id']
            if pred_winner_id == true_winner_id:
                top1_hits += 1
                
            # Top 3 Prediction (Check if true winner is in top 3 predicted)
            # Or Check if Predicted Top 3 contains the True Winner? 
            # Usually "Top-3 Accuracy" means "Is the True Winner in the Top 3 predictions?"
            # Let's use that definition.
            top3_preds = sorted_group.iloc[:3]['horse_id'].values
            if true_winner_id in top3_preds:
                top3_hits += 1
                
        return {
            'top1_accuracy': top1_hits / total_races if total_races > 0 else 0,
            'top3_accuracy': top3_hits / total_races if total_races > 0 else 0
        }
