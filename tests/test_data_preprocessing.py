import pandas as pd
import pytest
from src.data_preprocessing import clean_data


def test_clean_data_temperature_mean_and_state():
    df = pd.DataFrame(
        {
            "State": ["A", "B"],
            "Jan": [10, 20],
            "Feb": [12, 22],
            "Mar": [14, 24],
        }
    )

    out = clean_data(df)
    assert "state_name" in out.columns
    assert "temperature" in out.columns
    # means: (10+12+14)/3 = 12, (20+22+24)/3 = 22
    assert pytest.approx(out.loc[out["state_name"] == "a", "temperature"].iat[0]) == 12
    assert pytest.approx(out.loc[out["state_name"] == "b", "temperature"].iat[0]) == 22


def test_clean_data_temperature_handles_missing_months_and_whitespace():
    df = pd.DataFrame(
        {
            "Region Name": ["X"],
            "jan": [5],
            "  feb  ": [7],
        }
    )
    out = clean_data(df)
    assert out["state_name"].iat[0] == "x"
    assert pytest.approx(out["temperature"].iat[0]) == 6


def test_clean_data_fertilizer_normalizes_and_deduplicates():
    df = pd.DataFrame(
        {
            "Crop": ["Maize", "Maize"],
            "N": [10, 10],
            "P": [5, 5],
            "K": [3, 3],
            "ph": [7, 7],
        }
    )
    out = clean_data(df)
    # should keep only one row per crop, lowercased
    assert out.shape[0] == 1
    assert "crop" in out.columns
    assert out["crop"].iat[0] == "maize"
    for col in ["n", "p", "k", "ph"]:
        assert col in out.columns


def test_clean_data_rainfall_normalizes_state_and_crop_and_keeps_rainfall():
    df = pd.DataFrame(
        {
            "State_Name": ["Karnataka"],
            "Crop_Name": ["Rice"],
            "Rainfall": [123.4],
            "Area_in_Hectares": [100],
        }
    )
    out = clean_data(df)
    assert "state_name" in out.columns
    assert "crop" in out.columns
    assert "rainfall" in out.columns
    assert out["state_name"].iat[0] == "karnataka"
    assert out["crop"].iat[0] == "rice"
    assert out["rainfall"].iat[0] == 123.4
