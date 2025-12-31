from sklearn.metrics import mean_squared_error
import numpy as np

def evaluate(actual, predicted):
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    return rmse
