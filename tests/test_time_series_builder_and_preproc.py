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
