import pandas as pd
from src.merge_datasets import merge_all_datasets


def test_clean_data_and_merge(tmp_path, monkeypatch):
    raw_dir = tmp_path / 'raw'
    proc_dir = tmp_path / 'processed'
    raw_dir.mkdir()
    proc_dir.mkdir()

    # create a tiny cleaned_crop_data_with_year.csv in the temp processed dir
    proc_file = proc_dir / 'cleaned_crop_data_with_year.csv'
    crop = pd.DataFrame([
        {'state_name': 'andhra pradesh', 'crop': 'rice', 'year': 2015, 'production': 100},
        {'state_name': 'andhra pradesh', 'crop': 'rice', 'year': 2014, 'production': 120},
    ])
    crop.to_csv(proc_file, index=False)

    # create Final_Dataset_after_temperature.csv in temp raw dir
    final_temp = pd.DataFrame([
        {'state_name': 'andhra pradesh', 'crop': 'rice', 'rainfall': 654.34, 'temperature': 29.2}
    ])
    final_temp.to_csv(raw_dir / 'Final_Dataset_after_temperature.csv', index=False)

    # create Fertilizer.csv in temp raw dir
    fert = pd.DataFrame([
        {'Crop': 'Rice', 'N': 80, 'P': 40, 'K': 40}
    ])
    fert.to_csv(raw_dir / 'Fertilizer.csv', index=False)

    # run merge with explicit paths so we don't touch repo files
    merge_all_datasets(raw_dir=str(raw_dir), processed_dir=str(proc_dir), out_dir=str(tmp_path))

    out = tmp_path / 'final_dataset.csv'
    assert out.exists()
    df = pd.read_csv(out)
    # check merged columns
    assert 'rainfall' in df.columns
    assert 'temperature' in df.columns
    assert 'n' in df.columns or 'N' in df.columns
    # check that fertilizer values were attached
    assert df['production'].sum() == 220
