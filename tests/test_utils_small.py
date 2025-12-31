import pandas as pd
import numpy as np
from src import evaluation, forecast, recommender


def test_evaluate_rmse_zero():
    actual = [1, 2, 3]
    predicted = [1, 2, 3]
    rmse = evaluation.evaluate(actual, predicted)
    assert rmse == 0


def test_forecast_future():
    class Dummy:
        def forecast(self, steps=5):
            return list(range(steps))
    out = forecast.forecast_future(Dummy(), steps=3)
    assert out == [0, 1, 2]


def test_recommender_order():
    df = pd.DataFrame({
        'state_name': ['A','A','A','A'],
        'crop': ['X','Y','X','Z'],
        'yield_ton_per_hec': [10, 5, 20, 1]
    })
    best, worst = recommender.recommend_crops(df, 'A')
    assert 'X' in best.index
    assert best.index[0] == 'X'
