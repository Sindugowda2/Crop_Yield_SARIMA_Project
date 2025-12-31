import pandas as pd
from src import sarima_model


def test_train_sarima_short_series_returns_none():
    s = pd.Series([1,2,3])
    assert sarima_model.train_sarima(s) is None


def test_train_sarima_calls_sarimax(monkeypatch):
    class DummyModel:
        def __init__(self, series, **kwargs):
            self.series = series
        def fit(self, disp=False):
            return 'fitted'

    monkeypatch.setattr(sarima_model, 'SARIMAX', DummyModel)
    s = pd.Series(range(10))
    out = sarima_model.train_sarima(s)
    assert out == 'fitted'
