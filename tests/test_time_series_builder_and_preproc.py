import pandas as pd
import pytest
from src.time_series_builder import build_time_series
from src.data_preprocessing import prepare_sarima_series


def test_build_time_series_errors_missing_year():
    df = pd.DataFrame({'state_name':['A'], 'crop':['X'], 'yield':[1]})
    with pytest.raises(Exception):
        build_time_series(df, 'A', 'X')


def test_build_time_series_success():
    df = pd.DataFrame({'state_name':['A','A'], 'crop':['X','X'], 'year':[2019,2020], 'yield':[10,20]})
    ts = build_time_series(df, 'A', 'X')
    assert len(ts) == 2


def test_prepare_sarima_series_no_required_columns():
    df = pd.DataFrame({'state':['A'], 'crop_type':['X']})
    with pytest.raises(Exception):
        prepare_sarima_series(df, 'A', 'X')


def test_prepare_sarima_series_success():
    df = pd.DataFrame({'state_name':['A','A'], 'crop':['X','X'], 'year':[2019,2020], 'production_in_tons':[5,15]})
    ts = prepare_sarima_series(df, 'A', 'X')
    assert ts.sum() == 20


def test_build_time_series_column_case_insensitive_and_prod_cols():
    # Columns with different casing and different production column names
    df1 = pd.DataFrame({'State_Name':['A','A'], 'Crop':['X','X'], 'Year':[2019,2020], 'Yield':[10,20]})
    ts1 = build_time_series(df1, 'A', 'X')
    assert len(ts1) == 2
    assert ts1.sum() == 30

    df2 = pd.DataFrame({'State_Name':['A','A'], 'Crop':['X','X'], 'Year':[2019,2020], 'production_in_tons':[5,15]})
    ts2 = build_time_series(df2, 'A', 'X')
    assert len(ts2) == 2
    assert ts2.sum() == 20


def test_build_time_series_missing_production_column_raises():
    df = pd.DataFrame({'state_name':['A','A'], 'crop':['X','X'], 'year':[2019,2020]})
    with pytest.raises(Exception) as exc:
        build_time_series(df, 'A', 'X')
    assert 'No production column' in str(exc.value)


def test_build_time_series_no_matching_rows_raises():
    df = pd.DataFrame({'state_name':['B','B'], 'crop':['Y','Y'], 'year':[2019,2020], 'yield':[1,2]})
    with pytest.raises(Exception) as exc:
        build_time_series(df, 'A', 'X')
    assert 'No data found' in str(exc.value)


def test_build_time_series_non_numeric_production_raises():
    df = pd.DataFrame({'state_name':['A','A'], 'crop':['X','X'], 'year':[2019,2020], 'yield':['a','b']})
    with pytest.raises(Exception):
        build_time_series(df, 'A', 'X')


def test_build_time_series_unsorted_years_sorted_by_year():
    df = pd.DataFrame({'state_name':['A','A','A'], 'crop':['X','X','X'], 'year':[2020,2018,2019], 'yield':[20,5,10]})
    ts = build_time_series(df, 'A', 'X')
    # After sorting by year, the values should be [5,10,20]
    assert list(ts.values) == [5.0, 10.0, 20.0]


def test_build_time_series_missing_required_columns():
    df = pd.DataFrame({'state':['A'], 'crop_type':['X'], 'yr':[2019]})
    with pytest.raises(Exception) as exc:
        build_time_series(df, 'A', 'X')
    assert 'Missing required columns' in str(exc.value)
