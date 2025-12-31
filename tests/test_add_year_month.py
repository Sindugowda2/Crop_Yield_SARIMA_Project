import pandas as pd
import os
from pathlib import Path
import tempfile
import shutil

from src import add_year_month


def write_csv(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def test_manual_map_applied(tmp_path):
    # Prepare temp files
    data_dir = tmp_path / 'data'
    raw = data_dir / 'raw'
    proc = data_dir / 'processed'
    raw.mkdir(parents=True)
    proc.mkdir(parents=True)

    # crop has a state that needs mapping
    crop_df = pd.DataFrame({
        'state_name': ['Odisha', 'SomeState'],
        'crop': ['Wheat', 'Rice'],
        'crop_type': ['rabi', 'kharif'],
        'production_in_tons': [100, 200]
    })

    # rainfall has subdivision 'orissa' with year and months
    rain_df = pd.DataFrame({
        'subdivision': ['orissa', 'someother'],
        'Year': [2010, 2010],
        'jan': [10, 0], 'feb': [10,0], 'mar':[10,0], 'apr':[10,0], 'may':[10,0], 'jun':[10,0],
        'jul':[10,0], 'aug':[10,0], 'sep':[10,0], 'oct':[10,0], 'nov':[10,0], 'dec':[10,0]
    })

    # a manual CSV mapping (odisha -> orissa)
    manual_map_csv = pd.DataFrame({'state': ['odisha'], 'subdivision': ['orissa']})

    # write to temp paths and monkeypatch module constants
    crop_path = proc / 'cleaned_crop_data.csv'
    rain_path = raw / 'rainfall_validation.csv'
    out_path = proc / 'cleaned_crop_data_with_year.csv'
    manual_path = proc / 'manual_state_to_subdivision.csv'

    write_csv(crop_path, crop_df)
    write_csv(rain_path, rain_df)
    write_csv(manual_path, manual_map_csv)

    # patch module paths
    add_year_month.CROP_FILE = str(crop_path)
    add_year_month.RAINFALL_FILE = str(rain_path)
    add_year_month.OUT_FILE = str(out_path)
    add_year_month.MANUAL_MAP_FILE = str(manual_path)

    # run main
    add_year_month.main()

    # read output and assert years filled
    out = pd.read_csv(out_path)
    assert 'year' in out.columns
    assert out['year'].notna().any()
    # Odisha row should have year 2010
    od = out[out['state_name'].str.lower()=='odisha']
    assert int(od['year'].iloc[0]) == 2010

    # Seasonal rainfall for Odisha (rabi) should be computed
    assert 'seasonal_rainfall' in out.columns
    od_sr = od['seasonal_rainfall'].iloc[0]
    # expected rabi months sum (oct,nov,dec,jan,feb,mar) each 10 => 60
    assert float(od_sr) == 60.0


def test_load_manual_map_reads(tmp_path):
    proc = tmp_path / 'processed'
    proc.mkdir(parents=True)
    manual_map_csv = pd.DataFrame({'state': ['foo'], 'subdivision': ['bar']})
    p = proc / 'manual_state_to_subdivision.csv'
    manual_map_csv.to_csv(p, index=False)
    m = add_year_month.load_manual_map(str(p))
    assert isinstance(m, dict)
    assert m.get('foo') == 'bar'
