import pandas as pd
import numpy as np

# =====================================================
# INDEX BUILDER
# =====================================================

def build_indexes(df):

    df = df.copy()

    lap_index = {
        lap: group.reset_index(drop=True)
        for lap, group in df.groupby("lapNum")
    }

    summary = df.groupby("lapNum").agg({
        "rpm": "mean",
        "throttle": "mean",
        "brake": "mean"
    }).reset_index()

    summary["score"] = (
        summary["rpm"] * 0.4 +
        summary["throttle"] * 100 * 0.4 -
        summary["brake"] * 100 * 0.2
    )

    return {
        "lap_index": lap_index,
        "summary": summary
    }


# =====================================================
# LAP ACCESS
# =====================================================

def get_lap_data(indexes, lap_num):
    return indexes["lap_index"][lap_num]


# =====================================================
# BEST / WORST LAP
# =====================================================

def get_best_worst(summary):
    best = summary.loc[summary["score"].idxmax()]
    worst = summary.loc[summary["score"].idxmin()]
    return best, worst


# =====================================================
# DELTA ANALYSIS
# =====================================================

def compute_delta_to_best(df):

    lap_avg = df.groupby("lapNum")["rpm"].mean()
    best = lap_avg.max()

    return (lap_avg - best).reset_index(name="delta_rpm")


# =====================================================
# SECTOR ANALYSIS
# =====================================================

def compute_sector_summary(df):

    df = df.copy()
    df["sector"] = df.groupby("lapNum").cumcount() // 3 + 1

    return df.groupby(["lapNum", "sector"]).agg({
        "rpm": "mean",
        "throttle": "mean",
        "brake": "mean"
    }).reset_index()


# =====================================================
# CORNER DETECTION
# =====================================================

def detect_corners(df):
    df = df.copy()
    return df[df["brake"] > 0.3]


# =====================================================
# DRIVER STYLE
# =====================================================

def classify_driver_style(df):

    avg_throttle = df["throttle"].mean()
    avg_brake = df["brake"].mean()

    if avg_throttle > 0.85 and avg_brake < 0.3:
        return "Aggressive 🟥"
    elif avg_throttle < 0.6:
        return "Conservative 🟦"
    else:
        return "Balanced 🟩"