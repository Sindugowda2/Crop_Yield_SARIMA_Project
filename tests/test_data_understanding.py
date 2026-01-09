import pandas as pd
from src import data_understanding


def test_understand_data_runs(tmp_path, capsys):
    raw = tmp_path / "raw"
    raw.mkdir(parents=True)
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    path = raw / "Crop_production.csv"
    df.to_csv(path, index=False)

    # monkeypatch DATA_DIR
    old = data_understanding.DATA_DIR
    try:
        data_understanding.DATA_DIR = str(raw)
        data_understanding.understand_data()
        captured = capsys.readouterr()
        assert "Dataset Shape" in captured.out
    finally:
        data_understanding.DATA_DIR = old
