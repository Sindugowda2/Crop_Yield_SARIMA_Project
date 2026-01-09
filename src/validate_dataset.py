import sys
from src.data_loader import load_cleaned_dataset


def main():
    try:
        df, src = load_cleaned_dataset(prefer_enriched=True)
    except Exception as e:
        print(f"ERROR: Could not load cleaned dataset: {e}")
        sys.exit(2)

    print(f"Loaded dataset from: {src}")

    # check year
    year_col = None
    for c in df.columns:
        if "year" in c.lower():
            year_col = c
            break

    if year_col is None:
        print("FAIL: No 'year' column found in dataset.")
        sys.exit(3)

    missing_years = df[year_col].isna().sum()
    if missing_years > 0:
        print(f"FAIL: Found {missing_years} rows with missing year.")
        sys.exit(4)

    print("PASS: 'year' column present and no missing values.")

    # quick time-series build sanity check
    try:
        from src.time_series_builder import build_time_series

        state_col = [c for c in df.columns if "state" in c.lower()][0]
        crop_col = [
            c for c in df.columns if "crop" == c.lower() or c.lower() == "crop"
        ][0]
        sample_state = df[state_col].dropna().unique()[0]
        sample_crop = df[crop_col].dropna().unique()[0]
        ts = build_time_series(df, sample_state, sample_crop)
        if ts.empty:
            print("WARN: time-series built but empty")
        else:
            print(
                "PASS: time-series builder produced a series sample (length: {} )".format(
                    len(ts)
                )
            )

        # Known-case sanity check: Andaman & Nicobar Islands + Arecanut
        try:
            states = df[state_col].dropna().str.lower().unique()
            crops = df[crop_col].dropna().str.lower().unique()
            if "andaman and nicobar islands" in states and "arecanut" in crops:
                ts2 = build_time_series(df, "Andaman And Nicobar Islands", "Arecanut")
                if ts2.empty:
                    print(
                        "FAIL: Known sample (Andaman/Arecanut) produced empty series."
                    )
                    sys.exit(6)
                else:
                    print(
                        "PASS: Known sample (Andaman/Arecanut) produced a non-empty series (length: {})".format(
                            len(ts2)
                        )
                    )
        except Exception as e:
            print(f"WARN: Known-sample check failed: {e}")
    except Exception as e:
        print(f"FAIL: time-series builder failed: {e}")
        sys.exit(5)


if __name__ == "__main__":
    main()
