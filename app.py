import streamlit as st

from src.data_loader import load_data
from src.analysis import (
    build_indexes,
    get_lap_data,
    get_best_worst,
    generate_engine_report,
    prepare_data
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Race Engineering Dashboard",
    layout="wide"
)

st.title("🏎️ Race Engineering Platform")
st.caption("Telemetry-driven GT3 performance analysis")

# =====================================================
# LOAD DATA (CACHED + SAFE)
# =====================================================

@st.cache_data(show_spinner="Loading telemetry...")
def load():
    df = load_data()
    df = prepare_data(df)
    return df

df = load()

# =====================================================
# BUILD INDEXES (CACHE SAFE)
# =====================================================

@st.cache_data
def build(df):
    return build_indexes(df)

indexes = build(df)

lap_index = indexes["lap_index"]
summary = indexes["summary"]

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("System Status")
st.sidebar.success("✔ Data Loaded")
st.sidebar.success("✔ Analysis Engine Ready")

# =====================================================
# 🧠 ENGINE REPORT (TOP LEVEL INSIGHT)
# =====================================================

st.subheader("🧠 Engineer Report (Time Loss Breakdown)")

report = generate_engine_report(df)

if len(report) == 0:
    st.warning("No issues detected in dataset")
else:
    for r in report:
        st.markdown(
            f"""
            **Segment {r['segment']}**  
            ⏱ Time Loss: **-{r['time_loss']}s**  
            🧠 Cause: {r['reason']}
            """
        )

# =====================================================
# LAP SELECTION
# =====================================================

lap_list = sorted(lap_index.keys())
selected_lap = st.selectbox("Select Lap", lap_list)

lap_data = get_lap_data(indexes, selected_lap)

# =====================================================
# TELEMETRY VIEW (SIMPLIFIED)
# =====================================================

st.subheader(f"📊 Lap {selected_lap} Telemetry")

col1, col2, col3 = st.columns(3)

with col1:
    st.line_chart(lap_data["speed"])

with col2:
    st.line_chart(lap_data["throttle"])

with col3:
    st.line_chart(lap_data["brake"])

# =====================================================
# BEST / WORST LAP
# =====================================================

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

    st.write("Speed Comparison")

    st.line_chart({
        f"Lap {lap_a}": a["speed"],
        f"Lap {lap_b}": b["speed"]
    })

# =====================================================
# SUMMARY
# =====================================================

st.subheader("📊 Lap Summary")

st.dataframe(summary, use_container_width=True)