import pandas as pd
from src.time_series_builder import build_time_series

DATA_PATH = "data/processed/cleaned_crop_data.csv"

STATE = "Karnataka"
CROP = "Rice"

df = pd.read_csv(DATA_PATH)
print("✅ Dataset loaded")

series = build_time_series(df, STATE, CROP)

print("📈 Time Series Ready")
print(series.head())
