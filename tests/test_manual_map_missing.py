from src import add_year_month


def test_load_manual_map_missing():
    m = add_year_month.load_manual_map('nonexistent_file.csv')
    assert m is None
