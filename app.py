from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import os
import sys

# Add src to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.model import RaceModel
from src.data_loader import DataLoader
from src.feature_engineering import FeatureEngineer
from src.scraper import scrape_race_card

app = FastAPI(title="Horse Racing Predictor API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
model = RaceModel()
data_df = None
processed_df = None

DATA_PATH = "data/raw/races_cleaned.csv"
if not os.path.exists(DATA_PATH):
    DATA_PATH = None 

# Pydantic Models
class PredictionRequest(BaseModel):
    race_id: str

class ScrapeRequest(BaseModel):
    url: str

class HorseInfo(BaseModel):
    horse_id: str # Name
    jockey_id: str
    wakuban: int
    age: int
    sex: str
    weight: float

class CustomRaceRequest(BaseModel):
    race_info: dict
    horses: list[HorseInfo]

@app.on_event("startup")
def startup_event():
    global data_df, processed_df
    print("Loading Data and Model...")
    
    loader = DataLoader(DATA_PATH)
    data_df = loader.load_data()
    if 'race_id' in data_df.columns:
        data_df['race_id'] = data_df['race_id'].astype(str)
    
    fe = FeatureEngineer()
    processed_df = fe.fit_transform(data_df)
    
    print("Startup Complete")

@app.get("/api/races")
def get_races():
    """Returns a list of available races."""
    if data_df is None:
        return []
    
    races = []
    unique_races = data_df['race_id'].unique()
    
    for rid in unique_races:
        race_rows = data_df[data_df['race_id'] == rid]
        first_row = race_rows.iloc[0]
        
        races.append({
            "race_id": str(rid),
            "course": f"{first_row['course_type']} {first_row['distance']}m",
            "weather": first_row['weather'],
            "condition": first_row['track_condition'],
            "horses_count": len(race_rows)
        })
        
    return races

@app.get("/api/races/{race_id}")
def get_race_details(race_id: str):
    """Returns details and horses for a specific race."""
    if data_df is None:
        raise HTTPException(status_code=404, detail="No data loaded")
        
    race_rows = data_df[data_df['race_id'] == race_id]
    if race_rows.empty:
        raise HTTPException(status_code=404, detail="Race not found")
        
    horses = []
    for _, row in race_rows.iterrows():
        horses.append({
            "horse_id": row['horse_id'],
            "jockey_id": row['jockey_id'],
            "wakuban": int(row['wakuban']),
            "age": int(row['age']),
            "sex": row['sex'],
            "weight": float(row['weight']),
            "rank": int(row['rank']) if 'rank' in row else None
        })
        
    first = race_rows.iloc[0]
    race_info = {
        "race_id": race_id,
        "course": f"{first['course_type']} {first['distance']}m",
        "weather": first['weather'],
        "condition": first['track_condition']
    }
    
    return {"info": race_info, "horses": horses}

@app.post("/api/predict/{race_id}")
def predict_race(race_id: str):
    """Runs prediction for the race."""
    if processed_df is None:
         raise HTTPException(status_code=500, detail="Data not processed")
    
    race_rows = processed_df[processed_df['race_id'] == race_id]
    
    if race_rows.empty:
        raise HTTPException(status_code=404, detail="Race data not found for prediction")

    try:
        results = model.predict(race_rows)
        
        predictions = []
        scores = results['predicted_score'].values
        # Softmax for probabilities (inverted scores because lower is better)
        exp_scores = np.exp(-scores)
        probabilities = exp_scores / np.sum(exp_scores)
        
        for idx, row in results.iterrows():
            # We need to match probability back to row. 
            # results index should match prob index if order preserved.
            # Convert idx relative to start of array?
            # Actually iterrows returns index of original DF.
            # We better just assign column
            pass

        results['probability'] = probabilities * 100 # Percentage

        for _, row in results.iterrows():
            predictions.append({
                "horse_id": row['horse_id'],
                "score": float(row['predicted_score']),
                "confidence": float(row['probability'])
            })
            
        predictions.sort(key=lambda x: x['score'])
        
        return {"predictions": predictions}
        
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape_race")
def scrape_race_endpoint(request: ScrapeRequest):
    """Scrapes race info from a URL."""
    try:
        data = scrape_race_card(request.url)
        if not data:
             raise HTTPException(status_code=400, detail="Failed to scrape data. Check URL.")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict_custom")
def predict_custom(request: CustomRaceRequest):
    """Predicts rank for user-input race data."""
    try:
        race_info = request.race_info
        horses = request.horses
        
        rows = []
        for h in horses:
            row = {
                'race_id': 'custom',
                'horse_id': h.horse_id,
                'jockey_id': h.jockey_id,
                'wakuban': h.wakuban,
                'age': h.age,
                'sex': h.sex,
                'weight': h.weight,
                'distance': int(race_info.get('distance', 1600)),
                'course_type': race_info.get('course_type', 'Grass'),
                'weather': race_info.get('weather', 'Sunny'),
                'track_condition': race_info.get('condition', 'Good'),
                'trainer_id': 'Unknown' 
            }
            rows.append(row)
            
        df = pd.DataFrame(rows)
        
        fe = FeatureEngineer()
        # Use transform to use loaded encoders from training.
        df_processed = fe.transform(df) 
        
        results = model.predict(df_processed)
        
        # Calculate Confidence
        scores = results['predicted_score'].values
        # Invert scores (Lower Rank = Higher Prob)
        # Using a temperature scaling factor could help if scores are too spread or too close
        # But for now, simple exp(-score)
        exp_scores = np.exp(-scores)
        probabilities = exp_scores / np.sum(exp_scores)
        results['probability'] = probabilities * 100
        
        predictions = []
        # We need to map back to original horse names if FE obscured them
        # In this simple FE impl, horse_id might be LabelEncoded.
        # But 'results' is a copy of 'df_processed'. 
        # So we need to recover original names from 'df' (which has them)
        # Assuming order is preserved.
        
        for idx, row in results.iterrows():
            # idx corresponds to index in df (preserved through FE and Predict)
            original_horse = df.loc[idx]
            
            predictions.append({
                "horse_id": original_horse['horse_id'], # Use original name
                "wakuban": int(original_horse['wakuban']),
                "jockey_id": original_horse['jockey_id'],
                "score": float(row['predicted_score']),
                "confidence": float(row['probability'])
            })
            
        # Re-attach original metadata for display if needed (or frontend has it)
        # Sort by score (already sorted by model.predict but list append order preserved)
        # predictions.sort(key=lambda x: x['score'])
        
        return {"predictions": predictions}

    except Exception as e:
        import traceback
        import sys
        err_msg = f"Custom Prediction Error: {e}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        with open("backend_error.log", "w") as f:
            f.write(err_msg)
        raise HTTPException(status_code=500, detail=str(e))


# Config for serving static files (Frontend)
# Ensure this comes AFTER API routes

# Get absolute path to frontend/dist to ensure it works in any working directory
current_dir = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(current_dir, "frontend", "dist")

print(f"Checking for frontend/dist at: {dist_dir}")

if os.path.exists(dist_dir):
    print("Frontend build found! Serving static files...")
    # Mount assets
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
    # Serve SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in dist
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise serve index.html
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    print(f"Frontend build NOT found at {dist_dir}")
    @app.get("/")
    async def root():
        return {
            "message": "Frontend build not found. Please run 'npm run build' in frontend directory.",
            "search_path": dist_dir
        }


if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 to make it publicly accessible (needed for Docker/Render)
    # Port defaults to 8000 or uses PORT env var
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

