import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

print("📥 Loading main dataset...")

df = pd.read_csv(os.path.join(RAW_DIR, "Crop_production.csv"))

print("✅ Original shape:", df.shape)

# Drop unwanted column
if "Unnamed: 0" in df.columns:
    df.drop(columns=["Unnamed: 0"], inplace=True)

# Standardize text columns
df["State_Name"] = df["State_Name"].str.lower().str.strip()
df["Crop"] = df["Crop"].str.lower().str.strip()

# Handle missing values
df.fillna(df.median(numeric_only=True), inplace=True)

# Save cleaned data
output_path = os.path.join(PROCESSED_DIR, "cleaned_crop_data.csv")
df.to_csv(output_path, index=False)

print("✅ Cleaned dataset saved")
print("📊 Final shape:", df.shape)
