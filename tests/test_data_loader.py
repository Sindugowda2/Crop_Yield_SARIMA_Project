import pandas as pd
from src import data_loader


def write_csv(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def test_load_cleaned_dataset_prefers_enriched(tmp_path):
    proc = tmp_path / 'data' / 'processed'
    proc.mkdir(parents=True)
    cleaned = proc / 'cleaned_crop_data.csv'
    enriched = proc / 'cleaned_crop_data_with_year.csv'
    write_csv(cleaned, pd.DataFrame({'a':[1]}))
    write_csv(enriched, pd.DataFrame({'a':[2]}))

    # monkeypatch module paths
    import pytest
    pytest.importorskip('tests')
    # use monkeypatch fixture via pytest: set in test body manually
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    mp.setenv('DUMMY', '1')
    mp.setattr(data_loader, 'PROCESSED_DIR', str(proc))
    try:
        df, src = data_loader.load_cleaned_dataset(prefer_enriched=True)
    finally:
        mp.undo()

    assert src == 'enriched'
    assert df['a'].iloc[0] == 2


def test_load_cleaned_dataset_falls_back(tmp_path):
    proc = tmp_path / 'data' / 'processed'
    proc.mkdir(parents=True)
    cleaned = proc / 'cleaned_crop_data.csv'
    write_csv(cleaned, pd.DataFrame({'a':[3]}))

    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    mp.setattr(data_loader, 'PROCESSED_DIR', str(proc))
    try:
        df, src = data_loader.load_cleaned_dataset(prefer_enriched=True)
    finally:
        mp.undo()
    assert src == 'cleaned'
    assert df['a'].iloc[0] == 3
