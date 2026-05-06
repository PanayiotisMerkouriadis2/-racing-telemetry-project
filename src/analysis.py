import streamlit as st

from src.data_loader import load_data
from src.analysis import (
    build_indexes,
    get_lap_data,
    get_best_worst,
    compute_delta_to_best,
    compute_sector_summary,
    detect_corners,
    classify_driver_style
)

# =====================================================
# PAGE CONFIG (FAST + CLEAN UI)
# =====================================================

st.set_page_config(
    page_title="F1 Telemetry Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏎️ F1-Style Telemetry Analytics Engine")
st.caption("Cloud-based motorsport engineering dashboard")

# =====================================================
# LOAD DATA (CACHED FROM S3 / PARQUET)
# =====================================================

df = load_data()

# =====================================================
# BUILD INDEXES (RUNS ONCE ONLY)
# =====================================================

indexes = build_indexes(df)

lap_index = indexes["lap_index"]
summary = indexes["summary"]

# =====================================================
# SIDEBAR CONTROLS
# =====================================================

st.sidebar.title("Controls")

lap_list = sorted(lap_index.keys())
selected_lap = st.sidebar.selectbox("Select Lap", lap_list)

# =====================================================
# GET LAP DATA (FAST LOOKUP)
# =====================================================

lap_data = get_lap_data(indexes, selected_lap)

# =====================================================
# ================= DASHBOARD =================
# =====================================================

st.subheader("📊 Telemetry Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### RPM")
    st.line_chart(lap_data["rpm"])

with col2:
    st.markdown("### Throttle")
    st.line_chart(lap_data["throttle"])

with col3:
    st.markdown("### Brake")
    st.line_chart(lap_data["brake"])

# =====================================================
# LAP SUMMARY TABLE
# =====================================================

st.subheader("🏁 Lap Performance Summary")

st.dataframe(summary, use_container_width=True)

best, worst = get_best_worst(summary)

col1, col2 = st.columns(2)

with col1:
    st.success(f"🏆 Best Lap: {int(best['lapNum'])}")

with col2:
    st.warning(f"⚠️ Worst Lap: {int(worst['lapNum'])}")

# =====================================================
# LAP COMPARISON
# =====================================================

st.subheader("🔁 Lap Comparison")

if len(lap_list) >= 2:

    lap_a = st.selectbox("Lap A", lap_list, index=0, key="a")
    lap_b = st.selectbox("Lap B", lap_list, index=1, key="b")

    a = get_lap_data(indexes, lap_a)
    b = get_lap_data(indexes, lap_b)

    st.write("RPM Comparison")
    st.line_chart({
        f"Lap {lap_a}": a["rpm"],
        f"Lap {lap_b}": b["rpm"]
    })

    st.write("Throttle Comparison")
    st.line_chart({
        f"Lap {lap_a}": a["throttle"],
        f"Lap {lap_b}": b["throttle"]
    })

    st.write("Brake Comparison")
    st.line_chart({
        f"Lap {lap_a}": a["brake"],
        f"Lap {lap_b}": b["brake"]
    })

# =====================================================
# DELTA ANALYSIS (F1 FEATURE)
# =====================================================

st.subheader("⏱ Delta vs Best Lap")

delta_df = compute_delta_to_best(df)

st.line_chart(delta_df.set_index("lapNum"))

# =====================================================
# SECTOR ANALYSIS (F1 FEATURE)
# =====================================================

st.subheader("🏁 Sector Performance")

sector_df = compute_sector_summary(df)

st.dataframe(
    sector_df[sector_df["lapNum"] == selected_lap],
    use_container_width=True
)

# =====================================================
# CORNER DETECTION
# =====================================================

st.subheader("🧭 Corner Detection")

corners = detect_corners(df[df["lapNum"] == selected_lap])

st.dataframe(corners[["rpm", "throttle", "brake"]])

# =====================================================
# DRIVER STYLE CLASSIFICATION
# =====================================================

st.subheader("🧠 Driver Style")

style = classify_driver_style(df[df["lapNum"] == selected_lap])

st.success(f"Style: {style}")

# =====================================================
# ENGINEER INSIGHTS
# =====================================================

st.subheader("📈 Engineer Insights")

avg_brake = df["brake"].mean()
avg_throttle = df["throttle"].mean()

if avg_brake > 0.4:
    st.warning("⚠️ High braking detected (time loss risk)")

if avg_throttle < 0.6:
    st.warning("⚠️ Low throttle usage (poor acceleration zones)")

if avg_throttle > 0.85:
    st.success("🔥 Aggressive throttle usage detected")

if 0.6 <= avg_throttle <= 0.85 and avg_brake <= 0.4:
    st.success("✅ Balanced driving style")