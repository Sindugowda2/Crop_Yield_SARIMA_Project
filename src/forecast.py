def forecast_future(model, steps=5):
    forecast = model.forecast(steps=steps)
    return forecast
