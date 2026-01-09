import pandas as pd
import pytest
from src import validate_dataset


def test_loader_failure(monkeypatch):
    def bad_loader(prefer_enriched=True):
        raise Exception("boom")

    monkeypatch.setattr(validate_dataset, "load_cleaned_dataset", bad_loader)
    with pytest.raises(SystemExit) as e:
        validate_dataset.main()
    assert e.value.code == 2


def test_missing_year_column(monkeypatch):
    df = pd.DataFrame({"state_name": ["A"], "crop": ["X"]})

    def loader(prefer_enriched=True):
        return df, "enriched"

    monkeypatch.setattr(validate_dataset, "load_cleaned_dataset", loader)
    with pytest.raises(SystemExit) as e:
        validate_dataset.main()
    assert e.value.code == 3


def test_missing_year_values(monkeypatch):
    df = pd.DataFrame({"state_name": ["A"], "crop": ["X"], "year": [None]})

    def loader(prefer_enriched=True):
        return df, "enriched"

    monkeypatch.setattr(validate_dataset, "load_cleaned_dataset", loader)
    with pytest.raises(SystemExit) as e:
        validate_dataset.main()
    assert e.value.code == 4
