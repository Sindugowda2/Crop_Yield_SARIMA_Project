import pandas as pd
import os
from src.data_preprocessing import clean_data

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)


def merge_all_datasets(raw_dir=None, processed_dir=None, out_dir=None):
    print("Loading datasets...")

    RAW = raw_dir or RAW_DIR
    PROC = processed_dir or PROCESSED_DIR
    OUT = out_dir or OUT_DIR

    # Prefer the already-processed crop dataset with year if present
    crop_path = os.path.join(PROC, "cleaned_crop_data_with_year.csv")
    if os.path.exists(crop_path):
        crop = clean_data(pd.read_csv(crop_path))
    else:
        crop = clean_data(pd.read_csv(os.path.join(RAW, "Crop_production.csv")))

    # Use the final rainfall+temperature merged file if present
    final_temp_path = os.path.join(RAW, "Final_Dataset_after_temperature.csv")
    if os.path.exists(final_temp_path):
        rain_temp = clean_data(pd.read_csv(final_temp_path))
    else:
        rain_temp = clean_data(pd.read_csv(os.path.join(RAW, "Data_after_rainfall.csv")))
        # try to augment with temperature if available
        temp_path = os.path.join(RAW, "temperature.csv")
        if os.path.exists(temp_path):
            temp = clean_data(pd.read_csv(temp_path))
            # temp: state_name, temperature
            rain_temp = rain_temp.merge(temp, on='state_name', how='left')

    fertilizer = clean_data(pd.read_csv(os.path.join(RAW, "Fertilizer.csv")))

    print("Merging datasets...")

    # Merge crop with rainfall/temperature on state_name & crop (rain_temp is crop-level)
    df = crop.merge(rain_temp, on=["state_name", "crop"], how="left")

    # Fertilizer is crop-level; merge on crop only
    if 'crop' in fertilizer.columns:
        fert = fertilizer.rename(columns={c: c for c in fertilizer.columns})
        df = df.merge(fert, on=["crop"], how="left")

    output_path = os.path.join(OUT, "final_dataset.csv")
    df.to_csv(output_path, index=False)

    print(f"Final dataset saved: {output_path}")
    print("Final shape:", df.shape)

    # generate a small suitability report
    generate_suitability_report(df, out_dir=processed_dir)


def generate_suitability_report(df, min_years=5, out_dir=None):
    """Generate a CSV with counts of unique years per (state,crop) and a usability flag."""
    if not {'state_name','crop','year'}.issubset(set(df.columns)):
        print("Skipping suitability report: required columns not present (state_name,crop,year)")
        return

    grp = df.groupby(['state_name','crop'])['year'].nunique().reset_index()
    grp = grp.rename(columns={'year':'year_count'})
    grp['usable_for_sarima'] = grp['year_count'] >= min_years

    out_dir = out_dir or PROCESSED_DIR
    out = os.path.join(out_dir, 'dataset_suitability.csv')
    grp.to_csv(out, index=False)
    print(f"Suitability report saved: {out}")


if __name__ == "__main__":
    merge_all_datasets()
