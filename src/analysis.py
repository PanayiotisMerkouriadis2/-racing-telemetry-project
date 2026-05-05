import pandas as pd

def get_lap_data(df, lap_num):
    return df[df["lapNum"] == lap_num].reset_index(drop=True)


def compute_lap_stats(df):
    lap_summary = df.groupby("lapNum").agg({
        "rpm": "mean",
        "throttle": "mean",
        "brake": "mean"
    }).reset_index()

    lap_summary["score"] = (
        lap_summary["rpm"] * 0.4 +
        lap_summary["throttle"] * 100 * 0.4 -
        lap_summary["brake"] * 100 * 0.2
    )

    return lap_summary


def get_best_and_worst_lap(lap_summary):
    best = lap_summary.loc[lap_summary["score"].idxmax()]
    worst = lap_summary.loc[lap_summary["score"].idxmin()]
    return best, worst