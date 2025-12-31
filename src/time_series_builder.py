import pandas as pd

def build_time_series(df, state, crop):

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # ---- Auto-detect year column ----
    year_col = None
    for col in df.columns:
        if "year" in col:
            year_col = col
            break

    if year_col is None:
        raise Exception("❌ No YEAR column found in dataset!")

    # ---- Auto-detect yield column (prefer 'yield', fallback to 'production') ----
    yield_col = None
    for col in df.columns:
        if "yield" in col:
            yield_col = col
            break

    prod_col = None
    for col in df.columns:
        if col in ("production", "production_in_tons", "production_tons"):
            prod_col = col
            break

    if yield_col is None and prod_col is None:
        raise Exception("❌ No YIELD or PRODUCTION column found in dataset!")

    # ---- Required columns ----
    # ensure state and crop columns exist
    if not any('state' in c for c in df.columns):
        raise Exception("❌ Required column 'state_name' or 'state' missing")
    if not any('crop' in c for c in df.columns):
        raise Exception("❌ Required column 'crop' missing")

    # ---- Filter ----
    filtered_df = df[
        (df[[c for c in df.columns if 'state' in c][0]].str.lower() == state.lower()) &
        (df[[c for c in df.columns if 'crop' in c][0]].str.lower() == crop.lower())
    ]

    if filtered_df.empty:
        raise Exception("❌ No data for selected State & Crop")

    # ---- Build time series: prefer yield mean, otherwise use production sum ----
    if yield_col is not None:
        ts = (
            filtered_df
            .groupby(year_col)[yield_col]
            .mean()
            .sort_index()
        )
    else:
        ts = (
            filtered_df
            .groupby(year_col)[prod_col]
            .sum()
            .sort_index()
        )

    return ts
