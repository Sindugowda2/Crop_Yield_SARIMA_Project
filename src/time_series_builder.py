"""Utilities for building time series used by the SARIMA pipeline.

This module provides `build_time_series` which converts a tabular dataset
with columns for state, crop and year into a 1-indexed pandas Series of
production values suitable for time-series modeling.

Expected behavior and notes:
- Column names are handled case-insensitively: underscores and casing are
  normalized internally.
- Required columns: `state_name`, `crop`, `year` (case-insensitive).
- Production columns supported (in order of preference): `yield`,
  `production_in_tons`, `yield_ton_per_hec`.
- If a production column has non-numeric values, a clear exception is
  raised during conversion to float.
"""

import pandas as pd
from typing import Optional


def _ensure_lower_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with column names normalized to lowercase.

    This helps make the function tolerant to different input dataset
    column naming conventions used across the project.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    return df


def build_time_series(df: pd.DataFrame, state: str, crop: str) -> pd.Series:
    """Build a time-indexed pandas Series of production values.

    Parameters
    ----------
    df : pd.DataFrame
        Tabular data that must contain `state_name`, `crop` and `year` columns
        (case-insensitive). The production column can be one of a few accepted
        names and is selected automatically.
    state : str
        State name to filter the dataset by (matching is case-insensitive).
    crop : str
        Crop name to filter the dataset by (matching is case-insensitive).

    Returns
    -------
    pd.Series
        A 1-indexed Series of production values (float) where the index is a
        simple integer time index (1..n) and values are sorted by `year`.

    Raises
    ------
    Exception
        If required columns are missing, if no production column exists, if
        there are no rows matching the state/crop filter, or if production
        values cannot be converted to float.
    """
    df = _ensure_lower_cols(df)

    # Required columns
    required = {"state_name", "crop", "year"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        raise Exception(f"Missing required columns: {', '.join(sorted(missing))}")

    # Normalize string columns used for matching
    df["state_name"] = df["state_name"].astype(str).str.strip().str.lower()
    df["crop"] = df["crop"].astype(str).str.strip().str.lower()

    state = state.strip().lower()
    crop = crop.strip().lower()

    # Choose a production column (prefer 'yield', then 'production_in_tons', then 'yield_ton_per_hec')
    prod_candidates = ["yield", "production_in_tons", "yield_ton_per_hec"]
    prod_col: Optional[str] = next(
        (c for c in prod_candidates if c in df.columns), None
    )
    if prod_col is None:
        raise Exception(
            "No production column found (expected one of: yield, production_in_tons, yield_ton_per_hec)"
        )

    filtered = df[(df["state_name"] == state) & (df["crop"] == crop)]

    if filtered.empty:
        raise Exception(
            f"No data found for state='{state}' and crop='{crop}'. Rows in dataset: {len(df)}"
        )

    # Sort by year (ascending) and reset index
    filtered = filtered.sort_values(by="year").reset_index(drop=True)
    filtered["time_index"] = pd.RangeIndex(start=1, stop=len(filtered) + 1)

    # Convert production values to float; any invalid values will raise
    series = filtered[prod_col].astype(float)
    series.index = filtered["time_index"]

    return series
