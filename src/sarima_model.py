from statsmodels.tsa.statespace.sarimax import SARIMAX


def train_sarima(series):
    if len(series) < 8:
        return None

    model = SARIMAX(
        series,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 4),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    model_fit = model.fit(disp=False)
    return model_fit
