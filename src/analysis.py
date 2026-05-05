import pandas as pd

def get_lap_data(df, lap_num):
    return df[df["lapNum"] == lap_num].reset_index(drop=True)


def compute_lap_summary(df):
    summary = df.groupby("lapNum").agg({
        "rpm": "mean",
        "throttle": "mean",
        "brake": "mean"
    }).reset_index()

    summary["score"] = (
        summary["rpm"] * 0.3 +
        summary["throttle"] * 100 * 0.4 -
        summary["brake"] * 100 * 0.2
    )

    return summary