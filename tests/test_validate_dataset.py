from src.data_loader import load_cleaned_dataset
from src.time_series_builder import build_time_series


def test_enriched_dataset_has_year():
    df, src = load_cleaned_dataset(prefer_enriched=True)
    year_cols = [c for c in df.columns if "year" in c.lower()]
    assert year_cols, "No 'year' column found in dataset"
    year_col = year_cols[0]
    assert df[year_col].notna().all(), "Found missing year values in dataset"


def test_andaman_arecanut_series():
    df, src = load_cleaned_dataset(prefer_enriched=True)
    # skip test if known sample not present (allows local dev without full dataset)
    present = (
        (df["state_name"].str.lower() == "andaman and nicobar islands")
        & (df["crop"].str.lower() == "arecanut")
    ).any()
    if not present:
        import pytest

        pytest.skip("Andaman/Arecanut not present in dataset in this environment")

    ts = build_time_series(df, "Andaman And Nicobar Islands", "Arecanut")
    assert not ts.empty, "Known sample (Andaman/Arecanut) produced empty series"
    assert len(ts) >= 1
