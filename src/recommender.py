def recommend_crops(df, state):
    state_df = df[df["state_name"] == state]

    avg_yield = (
        state_df.groupby("crop")["yield_ton_per_hec"]
        .mean()
        .sort_values(ascending=False)
    )

    best = avg_yield.head(5)
    worst = avg_yield.tail(5)

    return best, worst
