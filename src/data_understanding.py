import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")


def understand_data():
    df = pd.read_csv(os.path.join(DATA_DIR, "Crop_production.csv"))

    print("\nDataset Shape:", df.shape)
    print("\nColumns:")
    print(df.columns)

    print("\nData Types:")
    print(df.dtypes)

    print("\nMissing Values:")
    print(df.isnull().sum())

    print("\nSample Rows:")
    print(df.head())


if __name__ == "__main__":
    understand_data()
