import pandas as pd
import numpy as np


def prepare_data(df):
    df = df.copy()
    if "dist" not in df.columns:
        df["dist"] = df.groupby("lapNum").cumcount()
    df["segment"] = (df["dist"] // 100).astype(int)
    return df


def build_indexes(df):
    df = df.copy()
    lap_index = {
        lap: group.reset_index(drop=True)
        for lap, group in df.groupby("lapNum")
    }
    summary = df.groupby("lapNum").agg(
        rpm=("rpm", "mean"),
        throttle=("throttle", "mean"),
        brake=("brake", "mean"),
        max_speed=("speed", "max"),
        avg_speed=("speed", "mean"),
        avg_gear=("gear", "mean"),
        lat_accel=("lat_accel", lambda x: x.abs().mean()),
        long_accel=("long_accel", lambda x: x.abs().mean()),
        lap_time=("time", "max"),
    ).reset_index()
    summary["score"] = (
        summary["rpm"] * 0.4 +
        summary["throttle"] * 100 * 0.4 -
        summary["brake"] * 100 * 0.2
    )
    return {"lap_index": lap_index, "summary": summary}


def get_lap_data(indexes, lap_num):
    return indexes["lap_index"].get(lap_num, pd.DataFrame())


def get_best_worst(summary):
    best = summary.loc[summary["score"].idxmax()]
    worst = summary.loc[summary["score"].idxmin()]
    return best, worst


def get_best_lap(df):
    lap_times = df.groupby("lapNum")["time"].max()
    return lap_times.idxmin()


def compute_segment_delta(df):
    seg = df.groupby(["lapNum", "segment"])["speed"].mean().reset_index()
    best_lap = get_best_lap(df)
    ref = seg[seg["lapNum"] == best_lap]
    merged = seg.merge(ref, on="segment", suffixes=("", "_ref"))
    merged["delta"] = merged["speed_ref"] - merged["speed"]
    return merged


def find_time_loss(delta_df):
    losses = delta_df.groupby("segment")["delta"].mean()
    return losses.sort_values(ascending=False).head(5)


def diagnose_segment(df, segment):
    seg = df[df["segment"] == segment]
    brake = seg["brake"].mean()
    throttle = seg["throttle"].mean()
    if brake > 0.4:
        return "Over-braking → braking too early or too hard"
    elif throttle < 0.5:
        return "Poor throttle application → late on power"
    else:
        return "Low minimum speed → slow corner entry"


def generate_engine_report(df):
    df = prepare_data(df)
    delta_df = compute_segment_delta(df)
    losses = find_time_loss(delta_df)
    report = []
    for seg, val in losses.items():
        reason = diagnose_segment(df, seg)
        report.append({
            "segment": int(seg),
            "time_loss": round(val, 3),
            "reason": reason,
        })
    return report


def classify_driver_style(df):
    avg_throttle = df["throttle"].mean()
    avg_brake = df["brake"].mean()
    if avg_throttle > 0.85 and avg_brake < 0.3:
        return "Aggressive 🟥"
    elif avg_throttle < 0.6:
        return "Conservative 🟦"
    else:
        return "Balanced 🟩"


def get_track_map_data(df):
    """Return averaged x/y per dist point with speed/brake/throttle for colouring."""
    return (
        df.groupby("dist")[["x", "y", "speed", "brake", "throttle", "zone", "zone_name"]]
        .mean(numeric_only=False)
        .reset_index()
    )