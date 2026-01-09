import pandas as pd


def _ensure_lower_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with column names normalized to lowercase."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    return df


def build_time_series(df, state, crop):
    df = _ensure_lower_cols(df)

    # Required columns
    required = {"state_name", "crop", "year"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        raise Exception(f"Missing required columns: {', '.join(sorted(missing))}")

    # Normalize string columns
    df["state_name"] = df["state_name"].astype(str).str.strip().str.lower()
    df["crop"] = df["crop"].astype(str).str.strip().str.lower()

    state = state.strip().lower()
    crop = crop.strip().lower()

    # Choose a production column (prefer 'yield', then 'production_in_tons', then 'yield_ton_per_hec')
    prod_candidates = ["yield", "production_in_tons", "yield_ton_per_hec"]
    prod_col = next((c for c in prod_candidates if c in df.columns), None)
    if prod_col is None:
        raise Exception("No production column found (expected one of: yield, production_in_tons, yield_ton_per_hec)")

    filtered = df[(df["state_name"] == state) & (df["crop"] == crop)]

    if filtered.empty:
        raise Exception(
            f"No data found for state='{state}' and crop='{crop}'. Rows in dataset: {len(df)}"
        )

    # Sort by year and reset index
    filtered = filtered.sort_values(by="year").reset_index(drop=True)
    filtered["time_index"] = pd.RangeIndex(start=1, stop=len(filtered) + 1)

    series = filtered[prod_col].astype(float)
    series.index = filtered["time_index"]

    return series
