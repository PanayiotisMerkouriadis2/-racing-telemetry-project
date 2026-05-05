import boto3
import pandas as pd
import streamlit as st

# =====================================================
# CONFIG
# =====================================================

BUCKET_NAME = "racing-telemetry-pany-01"
FILE_NAME = "AMGGT3-BRANDSHATCH.csv"

# =====================================================
# LOAD DATA FROM S3
# =====================================================

s3 = boto3.client("s3")

@st.cache_data
def load_data():
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
    df = pd.read_csv(obj["Body"])
    return df

df = load_data()

st.title("🏎️ AMG GT3 Telemetry Dashboard")

# =====================================================
# CLEANING (SAFE)
# =====================================================

required_cols = ["rpm", "throttle", "brake", "lapNum"]

for col in required_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["rpm", "throttle", "brake", "lapNum"])

df["rpm_norm"] = df["rpm"] / df["rpm"].max()

# =====================================================
# LAP SELECTION
# =====================================================

lap_list = sorted(df["lapNum"].unique())

selected_lap = st.selectbox("Select Lap", lap_list)

lap_data = df[df["lapNum"] == selected_lap].reset_index(drop=True)

st.subheader(f"Lap {selected_lap} Telemetry")

st.line_chart(lap_data["rpm_norm"])
st.line_chart(lap_data["throttle"])
st.line_chart(lap_data["brake"])

# =====================================================
# LAP COMPARISON
# =====================================================

st.subheader("🔁 Lap Comparison")

lap1 = st.selectbox("Lap 1", lap_list, index=0)
lap2 = st.selectbox("Lap 2", lap_list, index=1)

l1 = df[df["lapNum"] == lap1].reset_index(drop=True)
l2 = df[df["lapNum"] == lap2].reset_index(drop=True)

st.write("RPM Comparison")
st.line_chart({
    f"Lap {lap1}": l1["rpm_norm"],
    f"Lap {lap2}": l2["rpm_norm"]
})

st.write("Throttle Comparison")
st.line_chart({
    f"Lap {lap1}": l1["throttle"],
    f"Lap {lap2}": l2["throttle"]
})

st.write("Brake Comparison")
st.line_chart({
    f"Lap {lap1}": l1["brake"],
    f"Lap {lap2}": l2["brake"]
})

# =====================================================
# RACE ENGINEER INSIGHTS
# =====================================================

st.subheader("🏁 Race Engineer Insights")

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

best_lap = lap_summary.loc[lap_summary["score"].idxmax()]["lapNum"]
worst_lap = lap_summary.loc[lap_summary["score"].idxmin()]["lapNum"]

st.write(f"🏆 Best Lap: **Lap {int(best_lap)}**")
st.write(f"⚠️ Worst Lap: **Lap {int(worst_lap)}**")

avg_brake = df["brake"].mean()
avg_throttle = df["throttle"].mean()

if avg_brake > 0.4:
    st.warning("High braking detected — possible over-braking")

if avg_throttle < 0.6:
    st.warning("Low throttle usage — weak acceleration zones")

if avg_throttle > 0.8:
    st.success("Strong throttle usage — aggressive driving style")