import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")

CROP_FILE = os.path.join(PROC_DIR, "cleaned_crop_data.csv")
RAINFALL_FILE = os.path.join(RAW_DIR, "rainfall_validation.csv")
OUT_FILE = os.path.join(PROC_DIR, "cleaned_crop_data_with_year.csv")

MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]

# Optional external manual mapping CSV (state -> subdivision)
MANUAL_MAP_FILE = os.path.join(PROC_DIR, "manual_state_to_subdivision.csv")


def load_manual_map(path):
    """Load manual mapping CSV with columns 'state' and 'subdivision'.
    Returns a dict mapping normalized state -> normalized subdivision, or None.
    """
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        if "state" not in df.columns or "subdivision" not in df.columns:
            print(
                f"WARN: Manual map file {path} missing required columns 'state' and 'subdivision'"
            )
            return None
        # normalize and build dict
        mapping = {}
        for _, r in df.iterrows():
            s = normalize_text(r["state"])
            sub = normalize_text(r["subdivision"])
            if pd.isna(s) or pd.isna(sub):
                continue
            mapping[s] = sub
        return mapping
    except Exception as e:
        print(f"WARN: Failed to load manual map {path}: {e}")
        return None


def normalize_text(s):
    if pd.isna(s):
        return s
    s = str(s).lower().strip()
    s = s.replace("&", "and")
    # remove punctuation except whitespace
    s = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in s)
    s = " ".join(s.split())
    return s


def main():
    print("Loading files...")
    crop = pd.read_csv(CROP_FILE)
    rain = pd.read_csv(RAINFALL_FILE)

    print("Normalizing columns and names...")
    crop.columns = crop.columns.str.strip().str.lower()
    rain.columns = rain.columns.str.strip().str.lower()

    # normalize rainfall columns (already lowercased)
    rain = rain.rename(columns={c: c.strip() for c in rain.columns})
    # try to find the YEAR column name in rain file (columns are lowercased)
    year_col = None
    for c in rain.columns:
        if "year" in c:
            year_col = c
            break
    if year_col is None:
        raise SystemExit("❌ No YEAR column found in rainfall file")

    # Standardize names
    if "subdivision" in rain.columns:
        rain = rain.rename(columns={"SUBDIVISION": "subdivision"})
    if "subdivision" not in rain.columns and "state_name" in rain.columns:
        rain = rain.rename(columns={"state_name": "subdivision"})

    rain = rain.rename(columns={year_col: "year"})
    # month columns are already lowercased; we'll ensure missing months are added later

    # normalize values for join
    crop["state_name"] = crop["state_name"].apply(normalize_text)
    rain["subdivision"] = rain["subdivision"].apply(normalize_text)

    # compute seasonal rainfall per row in rain
    print("Computing seasonal rainfall metrics (kharif/rabi/whole_year)...")
    # ensure month cols exist in rainfall frame (fill missing with 0)
    for m in MONTHS:
        if m not in rain.columns:
            rain[m] = 0

    # seasonal definitions
    kharif = ["jun", "jul", "aug", "sep"]
    rabi = ["oct", "nov", "dec", "jan", "feb", "mar"]
    rain["kharif_rain"] = rain[kharif].sum(axis=1)
    rain["rabi_rain"] = rain[rabi].sum(axis=1)
    rain["whole_year_rain"] = rain[MONTHS].sum(axis=1)

    # keep only subdivision/year/kharif_rain/rabi_rain/whole_year_rain
    rain_small = rain[
        ["subdivision", "year", "kharif_rain", "rabi_rain", "whole_year_rain"]
    ].drop_duplicates()

    # make a simple mapping try exact merge first
    print("Merging datasets (state -> subdivision) ...")
    merged = crop.merge(
        rain_small, left_on="state_name", right_on="subdivision", how="left"
    )

    missing_years = merged["year"].isna().sum()
    print(f"Rows missing YEAR after exact match: {missing_years}")

    if missing_years > 0:
        # first try manual known mappings for problematic states
        print("Applying manual state -> subdivision mappings for known mismatches...")
        # prefer loading CSV mapping if present
        csv_map = load_manual_map(MANUAL_MAP_FILE)
        if csv_map:
            manual_map = csv_map
            print(
                f"Loaded manual map from {MANUAL_MAP_FILE} ({len(manual_map)} entries)"
            )
        else:
            manual_map = {
                "odisha": "orissa",
                "puducherry": "tamil nadu",
                "nagaland": "naga mani mizo tripura",
                "manipur": "naga mani mizo tripura",
                "mizoram": "naga mani mizo tripura",
                "dadra and nagar haveli": "gujarat region",
            }
        # map only where missing
        need_map_idx = merged[merged["year"].isna()].index
        merged.loc[need_map_idx, "subdivision_manual"] = merged.loc[
            need_map_idx, "state_name"
        ].map(manual_map)
        # merge manual mapped subdivisions
        merged = merged.merge(
            rain_small,
            left_on="subdivision_manual",
            right_on="subdivision",
            how="left",
            suffixes=("", "_manual"),
        )
        # prefer existing year, then manual
        if "year_manual" in merged.columns:
            merged["year"] = merged["year"].fillna(merged["year_manual"])
        merged["kharif_rain"] = merged["kharif_rain"].fillna(
            merged.get("kharif_rain_manual")
        )
        merged["rabi_rain"] = merged["rabi_rain"].fillna(merged.get("rabi_rain_manual"))
        merged["whole_year_rain"] = merged["whole_year_rain"].fillna(
            merged.get("whole_year_rain_manual")
        )
        # drop helper manual cols
        merged = merged.drop(
            columns=[c for c in merged.columns if c.endswith("_manual")]
        )

        # try fuzzy: match where subdivision contains state_name or vice versa
        still_missing_states = merged.loc[merged["year"].isna(), "state_name"].unique()
        if len(still_missing_states) > 0:
            print("Trying fuzzy matches for remaining unmatched states...")
            corrections = {}
            for s in still_missing_states:
                # look for any subdivision that contains this state_name as substring
                candidates = rain_small[
                    rain_small["subdivision"].str.contains(s, na=False)
                ]["subdivision"].unique()
                if len(candidates) == 1:
                    corrections[s] = candidates[0]
                elif len(candidates) > 1:
                    # choose the first candidate (best-effort)
                    corrections[s] = candidates[0]

            if corrections:
                print(
                    f"Found fuzzy matches for {len(corrections)} states. Applying corrections..."
                )
                merged["subdivision_fuzzy"] = merged["state_name"].map(corrections)
                # merge where subdivision_fuzzy is set (match on subdivision only to bring fuzzy year/rain)
                merged = merged.merge(
                    rain_small,
                    left_on=["subdivision_fuzzy"],
                    right_on=["subdivision"],
                    how="left",
                    suffixes=("", "_fuzzy"),
                )
                # prefer exact year, then fuzzy
                if "year_fuzzy" in merged.columns:
                    merged["year"] = merged["year"].fillna(merged["year_fuzzy"])
                merged["kharif_rain"] = merged["kharif_rain"].fillna(
                    merged.get("kharif_rain_fuzzy")
                )
                merged["rabi_rain"] = merged["rabi_rain"].fillna(
                    merged.get("rabi_rain_fuzzy")
                )
                merged["whole_year_rain"] = merged["whole_year_rain"].fillna(
                    merged.get("whole_year_rain_fuzzy")
                )
                merged = merged.drop(
                    columns=[c for c in merged.columns if c.endswith("_fuzzy")]
                )

    # Now, assign seasonal rainfall to each crop row based on crop_type
    def pick_seasonal_rain(row):
        ct = str(row.get("crop_type", "")).lower()
        if "kharif" in ct:
            return row.get("kharif_rain")
        if "rabi" in ct:
            return row.get("rabi_rain")
        # fallback to whole_year
        return row.get("whole_year_rain")

    merged["seasonal_rainfall"] = merged.apply(pick_seasonal_rain, axis=1)

    # Count still missing years
    still_missing = merged["year"].isna().sum()
    print(f"Remaining rows missing YEAR after fuzzy attempts: {still_missing}")

    # Save result
    print(f"Saving merged dataset to: {OUT_FILE}")
    merged.to_csv(OUT_FILE, index=False)
    print(
        "Done. Review the CSV and run tests; if many rows are missing YEAR, we should add a manual mapping table."
    )


if __name__ == "__main__":
    main()
