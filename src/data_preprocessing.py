def prepare_sarima_series(df, state, crop):
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # find columns
    def find_col(cols, candidates):
        # Prefer exact (case-insensitive) matches first, then substring matches
        # This avoids choosing 'crop_type' when 'crop' is present.
        for cand in candidates:
            for c in cols:
                if c.lower() == cand.lower():
                    return c
        for cand in candidates:
            for c in cols:
                if cand.lower() in c.lower():
                    return c
        return None

    cols = list(df.columns)
    state_col = find_col(cols, ["state_name", "state"])
    crop_col = find_col(cols, ["crop"])
    year_col = find_col(cols, ["year"])
    prod_col = find_col(cols, ["production", "production_in_tons", "production_tons"])

    if not state_col or not crop_col or not year_col or not prod_col:
        raise Exception(
            "Missing required columns for SARIMA preparation (state, crop, year, production)"
        )

    # filter (case-insensitive)
    filtered = df[
        (df[state_col].astype(str).str.lower() == state.lower())
        & (df[crop_col].astype(str).str.lower() == crop.lower())
    ]

    if filtered.empty:
        raise Exception("No data for selected State & Crop")

    # ensure year is integer index (work on a copy to avoid SettingWithCopyWarning)
    filtered = filtered.copy()
    filtered.loc[:, year_col] = filtered[year_col].astype(float).astype(int)

    # ensure production column is numeric (raise on invalid values)
    import pandas as pd

    try:
        filtered.loc[:, prod_col] = pd.to_numeric(filtered[prod_col], errors="raise")
    except Exception:
        raise Exception("Production column contains non-numeric values")

    ts = filtered.groupby(year_col)[prod_col].sum().sort_index()

    return ts


# New helper: clean_data
def clean_data(df):
    """Normalize a dataset (crop, rainfall, fertilizer, temperature) into a common structure.

    Heuristics:
    - fertilizer: has columns 'crop' and N,P,K
    - temperature: months 'jan'..'dec' present -> compute mean temperature per state
    - rainfall/final: contains 'rainfall' column and also 'crop' -> lower state and crop
    - crop production: contains 'year' and production columns

    Returns a dataframe with standardized column names tailored to input content.
    """

    df = df.copy()
    # normalize column names
    df.columns = df.columns.str.strip().str.lower()

    cols = set(df.columns)

    months = {
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "june",
        "july",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    }

    # Fertilizer dataset
    if {"n", "p", "k"}.issubset(cols) and "crop" in cols:
        df["crop"] = df["crop"].astype(str).str.lower().str.strip()
        # keep only relevant columns
        keep = ["crop"] + [c for c in ["n", "p", "k", "ph"] if c in df.columns]
        return df[keep].drop_duplicates(subset=["crop"]).reset_index(drop=True)

    # Temperature dataset (monthly columns present)
    if months.intersection(cols):
        # identify state column (first non-month column)
        state_col = None
        for c in df.columns:
            if c not in months:
                state_col = c
                break
        if state_col is None:
            # fallback to first column
            state_col = df.columns[0]
        # compute row-wise mean across months present
        month_cols = [c for c in df.columns if c in months]
        df["temperature"] = df[month_cols].astype(float).mean(axis=1)
        df["state_name"] = (
            df[state_col].astype(str).str.lower().str.replace("\n", " ").str.strip()
        )
        return (
            df[["state_name", "temperature"]]
            .drop_duplicates(subset=["state_name"])
            .reset_index(drop=True)
        )

    # Rainfall / Final dataset (contains 'rainfall')
    if "rainfall" in cols:
        # ensure state and crop columns
        state_col = None
        for c in ["state_name", "state"]:
            if c in df.columns:
                state_col = c
                break
        if not state_col:
            # try to find a column containing 'state'
            for c in df.columns:
                if "state" in c:
                    state_col = c
                    break
        crop_col = None
        for c in ["crop", "crop_name"]:
            if c in df.columns:
                crop_col = c
                break
        if not crop_col:
            for c in df.columns:
                if "crop" in c:
                    crop_col = c
                    break
        # normalize
        if state_col:
            df["state_name"] = df[state_col].astype(str).str.lower().str.strip()
        if crop_col:
            df["crop"] = df[crop_col].astype(str).str.lower().str.strip()
        # keep commonly relevant columns
        keep = [
            c
            for c in [
                "state_name",
                "crop",
                "crop_type",
                "rainfall",
                "area_in_hectares",
                "production_in_tons",
                "yield_ton_per_hec",
                "temperature",
            ]
            if c in df.columns
        ]
        return df[[c for c in keep if c in df.columns]].reset_index(drop=True)

    # Generic crop production dataset (has year and production)
    if "year" in cols and any(
        k in cols for k in ["production", "production_in_tons", "production_tons"]
    ):
        # find production column
        prod_col = None
        for c in ["production", "production_in_tons", "production_tons"]:
            if c in df.columns:
                prod_col = c
                break
        state_col = None
        for c in ["state_name", "state"]:
            if c in df.columns:
                state_col = c
                break
        crop_col = None
        for c in ["crop", "crop_name"]:
            if c in df.columns:
                crop_col = c
                break
        # normalize
        if state_col:
            df["state_name"] = df[state_col].astype(str).str.lower().str.strip()
        if crop_col:
            df["crop"] = df[crop_col].astype(str).str.lower().str.strip()
        df["year"] = df["year"].astype(float).astype(int)
        df["production"] = df[prod_col]
        keep = ["state_name", "crop", "year", "production"]
        for c in ["area_in_hectares", "yield_ton_per_hec", "crop_type"]:
            if c in df.columns:
                keep.append(c)
        return df[[c for c in keep if c in df.columns]].reset_index(drop=True)

    # fallback: just return lower-cased columns
    df = df.rename(columns={c: c.lower() for c in df.columns})
    return df.copy()
