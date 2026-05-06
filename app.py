import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from src.data_loader import load_data
from src.analysis import (
    build_indexes,
    get_lap_data,
    get_best_worst,
    generate_engine_report,
    prepare_data,
    classify_driver_style,
    get_track_map_data,
)

st.set_page_config(page_title="Race Engineering Dashboard", layout="wide")
st.title("🏎️ Race Engineering Platform")
st.caption("AMG GT3 · Brands Hatch GP · Telemetry Analysis")


def fmt_laptime(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"


# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data(show_spinner="Loading telemetry from AWS S3...")
def load():
    df = load_data()
    df = prepare_data(df)
    return df


df = load()


@st.cache_data
def build(df):
    return build_indexes(df)


indexes = build(df)
lap_index = indexes["lap_index"]
summary = indexes["summary"]


# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("⚙️ System Status")
st.sidebar.success("✔ Data Loaded")
st.sidebar.success("✔ Analysis Engine Ready")

st.sidebar.divider()

st.sidebar.subheader("Driver Style")
style = classify_driver_style(df)
st.sidebar.metric("Overall Style", style)

st.sidebar.divider()

best, worst = get_best_worst(summary)

st.sidebar.subheader("Session Overview")
st.sidebar.metric(
    "🏆 Best Lap",
    f"Lap {int(best['lapNum'])}",
    fmt_laptime(best["lap_time"]),
)
st.sidebar.metric(
    "⚠️ Worst Lap",
    f"Lap {int(worst['lapNum'])}",
    fmt_laptime(worst["lap_time"]),
)


# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Track Map",
    "📊 Telemetry",
    "🧠 Engineer Report",
    "📋 Lap Summary"
])


# =====================================================
# TAB 1 — TRACK MAP (FULLY FIXED)
# =====================================================
with tab1:
    st.subheader("🗺️ Brands Hatch GP — Track Map")

    map_col1, map_col2 = st.columns([3, 1])

    with map_col1:
        colour_by = st.radio(
            "Colour track by",
            ["speed", "brake", "throttle"],
            horizontal=True,
        )

    map_data = get_track_map_data(df).copy()

    # ✅ Normalize coordinates
    map_data["x"] = map_data["x"] - map_data["x"].min()
    map_data["y"] = map_data["y"] - map_data["y"].min()

    colour_map = {
        "speed": ("Speed (km/h)", "RdYlGn"),
        "brake": ("Brake Input", "RdYlGn_r"),
        "throttle": ("Throttle", "RdYlGn"),
    }

    label, cscale = colour_map[colour_by]

    fig_map = go.Figure()

    # ✅ Clean racing line (fixes ugly dots)
    fig_map.add_trace(go.Scatter(
        x=map_data["x"],
        y=map_data["y"],
        mode="lines",
        line=dict(width=4, color="white"),
        customdata=map_data.get("zone_name", None),
        hovertemplate=(
            f"<b>{label}</b>: %{{y:.1f}}<br>"
            "<extra></extra>"
        ),
        showlegend=False,
    ))

    # Corner labels
    corners_meta = [
        (60, 430, "Paddock Hill Bend"),
        (660, 910, "Druids"),
        (940, 1100, "Graham Hill Bend"),
        (1430, 1620, "Surtees"),
        (1920, 2050, "Pilgrim's Drop"),
        (2140, 2330, "Stirling's"),
        (2430, 2680, "Clark Curve"),
        (2790, 2960, "Dingle Dell"),
        (3060, 3220, "Hawthorn Bend"),
        (3370, 3450, "Westfield"),
        (3660, 3820, "Clearways"),
    ]

    annotations = []

    for c_start, c_end, name in corners_meta:
        mid_dist = (c_start + c_end) / 2
        closest = map_data.iloc[
            (map_data["dist"] - mid_dist).abs().idxmin()
        ]

        annotations.append(dict(
            x=float(closest["x"]),
            y=float(closest["y"]),
            text=f"<b>{name}</b>",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#ffffff",
            ax=30,
            ay=-25,
            font=dict(color="white", size=10),
            bgcolor="rgba(30,30,30,0.75)",
            bordercolor="#555",
            borderwidth=1,
        ))

    fig_map.update_layout(
        annotations=annotations,
        paper_bgcolor="#0e0e0e",
        plot_bgcolor="#0e0e0e",
        height=520,
        margin=dict(l=10, r=10, t=10, b=10),

        # 🔥 CRITICAL FIX (prevents distortion)
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, autorange="reversed"),

        showlegend=False,
    )

    st.plotly_chart(fig_map, use_container_width=True)

    with map_col2:
        st.markdown("#### Corner Info")

        corner_stats = []
        for c_start, c_end, name in corners_meta:
            seg = df[(df["dist"] >= c_start) & (df["dist"] <= c_end)]
            if not seg.empty:
                corner_stats.append({
                    "Corner": name,
                    "Min Speed": f"{seg['speed'].min():.0f} km/h",
                    "Max Brake": f"{seg['brake'].max():.2f}",
                    "Avg Throttle": f"{seg['throttle'].mean():.2f}",
                })

        st.dataframe(
            pd.DataFrame(corner_stats),
            use_container_width=True,
            hide_index=True,
        )


# =====================================================
# TAB 2 — TELEMETRY
# =====================================================
with tab2:
    lap_list = sorted(lap_index.keys())
    selected_lap = st.selectbox("Select Lap", lap_list)

    lap_data = get_lap_data(indexes, selected_lap)

    st.subheader(f"📊 Lap {selected_lap} Telemetry")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Max Speed", f"{lap_data['speed'].max():.0f} km/h")
        st.line_chart(lap_data.set_index("dist")["speed"])

    with col2:
        st.metric("Avg Throttle", f"{lap_data['throttle'].mean():.2%}")
        st.line_chart(lap_data.set_index("dist")["throttle"])

    with col3:
        st.metric("Avg Brake", f"{lap_data['brake'].mean():.2%}")
        st.line_chart(lap_data.set_index("dist")["brake"])

    st.subheader("RPM & Gear")

    col4, col5 = st.columns(2)

    with col4:
        st.line_chart(lap_data.set_index("dist")["rpm"])

    with col5:
        st.line_chart(lap_data.set_index("dist")["gear"])

    st.subheader("🔁 Lap Comparison")

    if len(lap_list) >= 2:
        lap_a = st.selectbox("Lap A", lap_list, index=0, key="a")
        lap_b = st.selectbox("Lap B", lap_list, index=1, key="b")

        a = get_lap_data(indexes, lap_a)
        b = get_lap_data(indexes, lap_b)

        st.line_chart({
            f"Lap {lap_a}": a.set_index("dist")["speed"],
            f"Lap {lap_b}": b.set_index("dist")["speed"],
        })


# =====================================================
# TAB 3 — ENGINEER REPORT
# =====================================================
with tab3:
    st.subheader("🧠 Engineer Report — Time Loss Breakdown")

    report = generate_engine_report(df)

    if not report:
        st.warning("No issues detected in dataset")
    else:
        for r in report:
            with st.expander(f"Segment {r['segment']} — -{r['time_loss']}s"):
                st.markdown(f"**Cause:** {r['reason']}")


# =====================================================
# TAB 4 — LAP SUMMARY
# =====================================================
with tab4:
    st.subheader("📋 Full Lap Summary")

    display_cols = [
        "lapNum",
        "lap_time",
        "max_speed",
        "avg_speed",
        "avg_gear",
        "throttle",
        "brake",
        "lat_accel",
        "score",
    ]

    display_cols = [c for c in display_cols if c in summary.columns]

    summary_display = summary[display_cols].copy()

    if "lap_time" in summary_display.columns:
        summary_display["lap_time"] = summary_display["lap_time"].apply(fmt_laptime)

    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True,
    )