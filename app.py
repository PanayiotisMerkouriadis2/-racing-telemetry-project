import streamlit as st
import boto3
import pandas as pd

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Racing Telemetry Dashboard",
    layout="wide"
)

st.title("🏎️ Racing Telemetry Analytics Platform")
st.caption("Cloud-based motorsport telemetry system powered by AWS S3")

# =====================================================
# AWS CONNECTION (STREAMLIT SECRETS)
# =====================================================

AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["AWS_DEFAULT_REGION"]

BUCKET_NAME = "racing-telemetry-pany-01"
FILE_NAME = "AMGGT3-BRANDSHATCH.csv"

# =====================================================
# LOAD DATA FROM S3
# =====================================================

@st.cache_data
def load_data():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
    df = pd.read_csv(obj["Body"])

    return df

df = load_data()

# =====================================================
# CLEANING
# =====================================================

required_cols = ["rpm", "throttle", "brake", "lapNum"]

for col in required_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required_cols)

# Prevent divide-by-zero crash
rpm_max = df["rpm"].max()
df["rpm_norm"] = df["rpm"] / rpm_max if rpm_max != 0 else 0

# =====================================================
# SIDEBAR STATUS
# =====================================================

st.sidebar.title("System Status")
st.sidebar.success("✔ AWS Connected")
st.sidebar.success("✔ Data Loaded")
st.sidebar.success("✔ Dashboard Running")

# =====================================================
# LAP SELECTION
# =====================================================

lap_list = sorted(df["lapNum"].unique())

selected_lap = st.selectbox(
    "Select Lap",
    lap_list,
    key="lap_select_main"
)

lap_data = df[df["lapNum"] == selected_lap].reset_index(drop=True)

# =====================================================
# TELEMETRY VIEW
# =====================================================

st.subheader(f"📊 Lap {selected_lap} Telemetry")

col1, col2, col3 = st.columns(3)

with col1:
    st.line_chart(lap_data["rpm_norm"])

with col2:
    st.line_chart(lap_data["throttle"])

with col3:
    st.line_chart(lap_data["brake"])

# =====================================================
# LAP COMPARISON (SAFE VERSION)
# =====================================================

st.subheader("🔁 Lap Comparison")

if len(lap_list) >= 2:

    lap1 = st.selectbox("Lap 1", lap_list, index=0, key="lap1")
    lap2 = st.selectbox("Lap 2", lap_list, index=1, key="lap2")

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

else:
    st.info("Not enough laps for comparison.")

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

best_lap = lap_summary.loc[lap_summary["score"].idxmax(), "lapNum"]
worst_lap = lap_summary.loc[lap_summary["score"].idxmin(), "lapNum"]

st.success(f"🏆 Best Lap: Lap {int(best_lap)}")
st.warning(f"⚠️ Worst Lap: Lap {int(worst_lap)}")

avg_brake = df["brake"].mean()
avg_throttle = df["throttle"].mean()

if avg_brake > 0.4:
    st.warning("High braking detected (possible over-braking)")

if avg_throttle < 0.6:
    st.warning("Low throttle usage (weak acceleration zones)")

if avg_throttle > 0.85:
    st.success("Strong throttle performance detected")