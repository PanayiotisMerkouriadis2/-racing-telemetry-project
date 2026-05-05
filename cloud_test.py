import boto3
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# CONFIG
# =====================================================

BUCKET_NAME = "racing-telemetry-pany-01"
FILE_NAME = "AMGGT3-BRANDSHATCH.csv"

# =====================================================
# CONNECT TO AWS S3
# =====================================================

s3 = boto3.client("s3")

print("Connecting to AWS S3...")

obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
df = pd.read_csv(obj["Body"])

print("\n✅ Data loaded successfully")
print(df.head())

# =====================================================
# CLEANING (SAFE SCHEMA HANDLING)
# =====================================================

df = df.reset_index(drop=True)

expected_cols = ["rpm", "throttle", "brake", "steering", "gear", "lapNum"]

for col in expected_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["rpm", "throttle", "brake"])

# =====================================================
# LAP PERFORMANCE ANALYSIS
# =====================================================

print("\n🏁 Lap Summary:")

lap_summary = df.groupby("lapNum").agg({
    "rpm": "mean",
    "throttle": "mean",
    "brake": "mean"
}).reset_index()

# Performance score model (simple telemetry heuristic)
lap_summary["performance_score"] = (
    lap_summary["rpm"] * 0.4 +
    lap_summary["throttle"] * 100 * 0.4 -
    lap_summary["brake"] * 100 * 0.2
)

best_lap = lap_summary.loc[lap_summary["performance_score"].idxmax()]
worst_lap = lap_summary.loc[lap_summary["performance_score"].idxmin()]

print(lap_summary)

print("\n🏆 Best Lap:")
print(best_lap)

print("\n❌ Worst Lap:")
print(worst_lap)

# =====================================================
# NORMALISATION
# =====================================================

df["rpm_norm"] = df["rpm"] / df["rpm"].max()

# =====================================================
# MULTI-LAP TELEMETRY DASHBOARD
# =====================================================

fig, axs = plt.subplots(3, 1, figsize=(14, 8), sharex=True)

# RPM
for lap in df["lapNum"].unique():
    lap_data = df[df["lapNum"] == lap].reset_index(drop=True)
    axs[0].plot(lap_data.index, lap_data["rpm"] / lap_data["rpm"].max(), label=f"Lap {lap}")

axs[0].set_title("Engine RPM (Normalised)")
axs[0].legend()
axs[0].grid(True)

# THROTTLE
for lap in df["lapNum"].unique():
    lap_data = df[df["lapNum"] == lap].reset_index(drop=True)
    axs[1].plot(lap_data.index, lap_data["throttle"], label=f"Lap {lap}")

axs[1].set_title("Throttle Input")
axs[1].legend()
axs[1].grid(True)

# BRAKE
for lap in df["lapNum"].unique():
    lap_data = df[df["lapNum"] == lap].reset_index(drop=True)
    axs[2].plot(lap_data.index, lap_data["brake"], label=f"Lap {lap}")

axs[2].set_title("Brake Input")
axs[2].set_xlabel("Lap Progression")
axs[2].legend()
axs[2].grid(True)

plt.suptitle("AMG GT3 - Multi-Lap Telemetry Dashboard", fontsize=16)
plt.tight_layout()
plt.show()

# =====================================================
# BEST VS WORST LAP COMPARISON
# =====================================================

best_lap_num = int(best_lap["lapNum"])
worst_lap_num = int(worst_lap["lapNum"])

best = df[df["lapNum"] == best_lap_num].reset_index(drop=True)
worst = df[df["lapNum"] == worst_lap_num].reset_index(drop=True)

fig, axs = plt.subplots(3, 1, figsize=(14, 9), sharex=True)

# RPM comparison
axs[0].plot(best.index, best["rpm"] / best["rpm"].max(), label="Best Lap")
axs[0].plot(worst.index, worst["rpm"] / worst["rpm"].max(), label="Worst Lap")
axs[0].set_title("RPM Comparison")
axs[0].legend()
axs[0].grid(True)

# Throttle comparison
axs[1].plot(best.index, best["throttle"], label="Best Lap")
axs[1].plot(worst.index, worst["throttle"], label="Worst Lap")
axs[1].set_title("Throttle Comparison")
axs[1].legend()
axs[1].grid(True)

# Brake comparison
axs[2].plot(best.index, best["brake"], label="Best Lap")
axs[2].plot(worst.index, worst["brake"], label="Worst Lap")
axs[2].set_title("Brake Comparison")
axs[2].set_xlabel("Lap Progression")
axs[2].legend()
axs[2].grid(True)

plt.suptitle("Best vs Worst Lap Analysis - AMG GT3 Brands Hatch", fontsize=16)
plt.tight_layout()
plt.show()