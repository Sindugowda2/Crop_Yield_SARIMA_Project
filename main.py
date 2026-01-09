from src.data_loader import load_cleaned_dataset_df
from src.time_series_builder import build_time_series
from src.sarima_model import train_sarima

STATE = "karnataka"
CROP = "rice"

# Load data
df = load_cleaned_dataset_df()
print("✅ Dataset loaded")

# Build time series
series = build_time_series(df, STATE, CROP)
print("📈 Time Series Ready")

# Train SARIMA model
model = train_sarima(series)
print("✅ SARIMA model trained")
