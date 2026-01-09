import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")


def load_final_dataset():
    return pd.read_csv(os.path.join(DATA_DIR, "final_dataset.csv"))


def _cleaned_paths():
    cleaned = os.path.join(PROCESSED_DIR, "cleaned_crop_data.csv")
    enriched = os.path.join(PROCESSED_DIR, "cleaned_crop_data_with_year.csv")
    return cleaned, enriched


def load_cleaned_dataset(prefer_enriched: bool = True):
    """Load cleaned crop dataset.

    Returns (df, source) where source is 'enriched' or 'cleaned'.
    If prefer_enriched=True and the enriched file exists it will be used.
    """
    cleaned_path, enriched_path = _cleaned_paths()

    if prefer_enriched and os.path.exists(enriched_path):
        df = pd.read_csv(enriched_path)
        return df, "enriched"

    if os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
        return df, "cleaned"

    raise FileNotFoundError(
        f"Neither cleaned dataset nor enriched dataset found in {PROCESSED_DIR}"
    )


def load_cleaned_dataset_df(prefer_enriched: bool = True):
    """Backward-compatible helper: returns only the DataFrame (prefers enriched when available)."""
    df, _ = load_cleaned_dataset(prefer_enriched=prefer_enriched)
    return df
