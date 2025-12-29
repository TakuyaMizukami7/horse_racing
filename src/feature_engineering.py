import pandas as pd
import numpy as np
import os
import pickle

class FeatureEngineer:
    def __init__(self, output_dir: str = 'data/processed'):
        self.output_dir = output_dir
        self.target_encodings = {}
        self.global_mean = 8.0 # Default fallback
        # Categorical columns to target encode
        self.cat_cols = ['course_type', 'weather', 'track_condition', 'sex', 'jockey_id', 'trainer_id', 'horse_id']
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def fit(self, df: pd.DataFrame):
        """Calculates target statistics and lag features."""
        # Calculate global mean rank
        if 'rank' in df.columns:
            # Drop rows with NaN rank for calculation
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
            valid_df = df.dropna(subset=['rank'])
            
            self.global_mean = valid_df['rank'].mean()
            
            # --- Speed Index Calculation ---
            # Speed = Distance / Time
            if 'race_time' in valid_df.columns:
                valid_df['speed'] = valid_df['distance'] / valid_df['race_time']
                
                # Group by condition to establish baselines
                group_cols = ['course_type', 'distance', 'track_condition']
                self.speed_stats = valid_df.groupby(group_cols)['speed'].agg(['mean', 'std']).to_dict('index')
                
                # Calculate current speed index for all training rows to produce lag features (for last_horse_speed)
                def get_stats(row):
                    key = (row['course_type'], row['distance'], row['track_condition'])
                    return self.speed_stats.get(key, {'mean': np.nan, 'std': np.nan})
                    
                stats_df = valid_df.apply(get_stats, axis=1, result_type='expand')
                valid_df['speed_index'] = (valid_df['speed'] - stats_df['mean']) / (stats_df['std'] + 1e-6)
                valid_df['speed_index'] = valid_df['speed_index'].fillna(0).clip(-3, 3)
                
                # Get last known speed index for inference
                # Sort by race_id to ensure 'last' is actually last in time
                if 'race_id' in valid_df.columns:
                    valid_df = valid_df.sort_values('race_id')

                last_records = valid_df.drop_duplicates(subset=['horse_id'], keep='last')
                self.last_horse_speed = last_records.set_index('horse_id')['speed_index'].to_dict()

            # For 'last_known_ranks' (for Inference):
            valid_df = valid_df.sort_values('race_id') # Ensure sorted for last records
            last_records = valid_df.drop_duplicates(subset=['horse_id'], keep='last')
            self.last_horse_ranks = last_records.set_index('horse_id')['rank'].to_dict()
            
            for col in self.cat_cols:
                if col in valid_df.columns:
                    stats = valid_df.groupby(col)['rank'].mean()
                    self.target_encodings[col] = stats.to_dict()
        
        # Save encodings and history
        with open(os.path.join(self.output_dir, 'target_encodings.pkl'), 'wb') as f:
            pickle.dump({
                'map': self.target_encodings, 
                'mean': self.global_mean,
                'last_ranks': getattr(self, 'last_horse_ranks', {}),
                'speed_stats': getattr(self, 'speed_stats', {}),
                'last_speed': getattr(self, 'last_horse_speed', {})
            }, f)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies target encoding and fills lag features."""
        df_processed = df.copy()
        
        # Load if empty
        if not self.target_encodings:
            try:
                with open(os.path.join(self.output_dir, 'target_encodings.pkl'), 'rb') as f:
                    data = pickle.load(f)
                    self.target_encodings = data.get('map', {})
                    self.global_mean = data.get('mean', 8.0)
                    self.last_horse_ranks = data.get('last_ranks', {})
                    self.speed_stats = data.get('speed_stats', {})
                    self.last_horse_speed = data.get('last_speed', {})
            except FileNotFoundError:
                pass
                
        # --- Add Lag Features (Prev Rank & Prev Speed) ---
        
        # If we are in Training mode (indicated by existence of 'rank' and 'race_id'), 
        # we should compute it historically within the batch.
        is_training = 'rank' in df_processed.columns and 'race_id' in df_processed.columns and len(df_processed) > 1000
        
        if is_training:
            df_temp = df_processed.sort_values('race_id')
            
            # Prev Rank
            df_processed['prev_rank'] = df_temp.groupby('horse_id')['rank'].shift(1)
            
            # Prev Speed Index
            if 'race_time' in df_temp.columns:
                # We need to re-calculate speed_index for the batch to shift it
                # Recalculate speed (local)
                df_temp['speed'] = df_temp['distance'] / df_temp['race_time']
                
                def get_stats_t(row):
                    key = (row['course_type'], row['distance'], row['track_condition'])
                    stats = self.target_encodings.get('speed_stats', {}).get(key) # This might be wrong access pattern
                    # Self.speed_stats is dict of dicts?
                    return self.speed_stats.get(key, {'mean': np.nan, 'std': np.nan})

                # Note: self.speed_stats should be populated if we just called fit. 
                # If we are in transform-only (inference) but passed a large batch, we rely on loaded stats.
                
                # Optimized apply/lookup
                # Create a key Series
                keys = list(zip(df_temp['course_type'], df_temp['distance'], df_temp['track_condition']))
                # Map keys to mean/std
                means = [self.speed_stats.get(k, {'mean':np.nan})['mean'] for k in keys]
                stds = [self.speed_stats.get(k, {'std':np.nan})['std'] for k in keys]
                
                df_temp['speed_index'] = (df_temp['speed'] - means) / (np.array(stds) + 1e-6)
                df_temp['speed_index'] = df_temp['speed_index'].fillna(0).clip(-3, 3)
                
                df_processed['prev_speed_index'] = df_temp.groupby('horse_id')['speed_index'].shift(1)
            else:
                df_processed['prev_speed_index'] = 0
                
        else:
             # Inference Time: Look up last known info
             df_processed['prev_rank'] = df_processed['horse_id'].map(getattr(self, 'last_horse_ranks', {}))
             df_processed['prev_speed_index'] = df_processed['horse_id'].map(getattr(self, 'last_horse_speed', {}))
        
        # Fill NaN (First time runners or unknown)
        df_processed['prev_rank'] = df_processed['prev_rank'].fillna(self.global_mean) 
        df_processed['prev_speed_index'] = df_processed['prev_speed_index'].fillna(0)

        for col in self.cat_cols:
            if col in df_processed.columns:
                mapping = self.target_encodings.get(col, {})
                df_processed[col] = df_processed[col].map(mapping).fillna(self.global_mean)
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(self.global_mean)
                
        return df_processed

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.fit(df)
        return self.transform(df)
