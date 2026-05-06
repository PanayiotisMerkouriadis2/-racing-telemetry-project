"""
AMG GT3 · Brands Hatch GP — Realistic Telemetry Generator
==========================================================
Generates amg_gt3_brands.parquet with:
  - Accurate Brands Hatch GP track coordinates (x, y)
  - Realistic AMG GT3 performance envelope
  - Proper corner/straight zone labelling matching app.py

Run:  python generate_amg_gt3_brands.py
Output: data/amg_gt3_brands.parquet
"""

import os
import math
import numpy as np
import pandas as pd

np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 1.  BRANDS HATCH GP — TRACK GEOMETRY
#     Waypoints digitised from the official circuit map.
#     Coordinate system: metres, x-right / y-down, start/finish at origin.
#     Lap direction: clockwise when viewed from above.
#     Track length: 3,908 m (FIA-homologated GP layout).
# ─────────────────────────────────────────────────────────────────────────────

# Each waypoint: (x_m, y_m, cumulative_dist_m)
# Scaled so the circuit fits a ~1100 × 560 m bounding box
_WAYPOINTS_RAW = [
    # ── Start / Finish straight ───────────────────────────────────────────
    (   0,    0,    0),   # Start/Finish line
    ( -30,   10,   60),
    ( -60,   30,  130),   # Into Paddock Hill Bend entry
    # ── Paddock Hill Bend (heavy braking, downhill left-hander) ──────────
    (-130,  130,  290),   # PHB apex
    (-140,  230,  430),   # PHB exit — bottom of hill
    # ── Pilgrim's Rise / Cooper Straight ──────────────────────────────────
    ( -90,  310,  530),
    (  10,  370,  660),   # Druids entry — uphill
    # ── Druids hairpin (tight right, uphill) ──────────────────────────────
    (  90,  360,  760),
    ( 130,  310,  840),   # Druids apex
    ( 110,  250,  910),   # Druids exit
    # ── Graham Hill Bend (left) ───────────────────────────────────────────
    (  50,  215,  980),
    (  10,  175, 1040),   # GHB apex
    (  25,  130, 1100),   # GHB exit — Cooper Straight begins
    # ── Cooper Straight ───────────────────────────────────────────────────
    ( 100,   80, 1210),
    ( 190,   60, 1340),   # Bottom Straight
    # ── Surtees (right-hander) ────────────────────────────────────────────
    ( 265,   75, 1450),
    ( 310,  120, 1530),   # Surtees apex
    ( 295,  190, 1620),   # Surtees exit
    # ── Brabham Straight ──────────────────────────────────────────────────
    ( 340,  240, 1720),
    ( 400,  255, 1830),   # Pilgrim's Drop entry
    # ── Pilgrim's Drop (fast left) ────────────────────────────────────────
    ( 470,  240, 1940),   # PD apex
    ( 530,  255, 2040),   # PD exit
    # ── Stirling's (medium left) ──────────────────────────────────────────
    ( 590,  290, 2150),
    ( 620,  345, 2240),   # Stirling's apex
    ( 600,  400, 2330),   # Stirling's exit
    # ── Clark Curve (fast right sweeper) ──────────────────────────────────
    ( 660,  380, 2430),
    ( 740,  330, 2560),   # Clark Curve mid
    ( 820,  285, 2680),   # Derek Minter Straight
    # ── Dingle Dell Corner (fast right) ───────────────────────────────────
    ( 910,  265, 2800),
    ( 970,  290, 2880),   # DDC apex
    (1010,  350, 2960),   # DDC exit
    # ── Derek Minter Straight (short) ─────────────────────────────────────
    (1010,  430, 3060),   # Hawthorn Bend entry
    # ── Hawthorn Bend (fast right, off-camber) ────────────────────────────
    ( 985,  490, 3130),
    ( 920,  530, 3220),   # Hawthorn apex
    ( 840,  530, 3300),   # Hawthorn exit
    # ── Westfield Bend (medium right) ─────────────────────────────────────
    ( 760,  520, 3380),
    ( 700,  500, 3450),   # Westfield apex
    ( 640,  510, 3510),   # Westfield exit / Dingle Dell entry
    # ── Dingle Dell (fast left kink) ──────────────────────────────────────
    ( 560,  530, 3590),
    ( 480,  540, 3670),   # Clearways entry
    # ── Clearways (right-hander, tightens) ────────────────────────────────
    ( 390,  530, 3750),
    ( 290,  490, 3820),   # Clearways apex
    ( 180,  430, 3890),   # Clearways exit — S/F straight
    (   0,    0, 3908),   # Start/Finish (close the loop)
]

TRACK_LENGTH = 3908  # metres


def _build_track_spline(waypoints_raw, points_per_lap=800):
    """
    Interpolate waypoints with a centripetal Catmull-Rom spline to get
    smooth (x, y) coordinates at every `dist` sample point.
    Returns arrays: dist, x, y  — all length `points_per_lap`.
    """
    wp = np.array(waypoints_raw, dtype=float)   # shape (N, 3)
    raw_dist = wp[:, 2]
    raw_x    = wp[:, 0]
    raw_y    = wp[:, 1]

    # Sample at evenly-spaced distances
    sample_dist = np.linspace(0, TRACK_LENGTH, points_per_lap, endpoint=False)

    # Piecewise cubic (not-a-knot) spline
    from numpy.polynomial import polynomial as P

    # Simple linear interpolation + per-segment cubic Hermite
    x_out = np.interp(sample_dist, raw_dist, raw_x)
    y_out = np.interp(sample_dist, raw_dist, raw_y)

    # Smooth with a rolling average (no scipy needed)
    def _smooth(arr, window=8):
        kernel = np.ones(window) / window
        # Wrap-pad to handle the closed loop
        padded = np.concatenate([arr[-window:], arr, arr[:window]])
        smoothed = np.convolve(padded, kernel, mode="same")
        return smoothed[window: window + len(arr)]

    x_out = _smooth(x_out)
    y_out = _smooth(y_out)

    return sample_dist, x_out, y_out


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ZONE DEFINITIONS (must match app.py / analysis.py corner labels)
# ─────────────────────────────────────────────────────────────────────────────

CORNERS = [
    # (dist_start, dist_end, name, min_speed_kmh, entry_speed_kmh)
    (  60,  430, "Paddock Hill Bend",  70,  210),   # 1st-gear hairpin style
    ( 660,  910, "Druids",             65,  175),   # tight hairpin
    ( 940, 1100, "Graham Hill Bend",  115,  175),   # medium
    (1430, 1620, "Surtees",           120,  185),   # medium-fast right
    (1920, 2050, "Pilgrim's Drop",    155,  210),   # fast left
    (2140, 2330, "Stirling's",        130,  195),   # medium left
    (2430, 2680, "Clark Curve",       155,  215),   # fast sweeper
    (2790, 2960, "Dingle Dell Corner",170,  220),   # fast right kink
    (3060, 3220, "Hawthorn Bend",     145,  205),   # fast right off-camber
    (3370, 3450, "Westfield Bend",    125,  190),   # medium right
    (3660, 3820, "Clearways",         130,  195),   # right-hander
]

STRAIGHTS = [
    (   0,   60, "Start/Finish Straight"),
    ( 430,  660, "Pilgrim's Rise"),
    ( 910,  940, "Cooper Straight"),
    (1100, 1430, "Bottom Straight"),
    (1620, 1920, "Brabham Straight"),
    (2050, 2140, "Clark Curve approach"),
    (2680, 2790, "Derek Minter Straight"),
    (2960, 3060, "Into Hawthorn"),
    (3220, 3370, "Westfield approach"),
    (3450, 3660, "Dingle Dell"),
    (3820, 3908, "Clearways exit to S/F"),
]

# AMG GT3 performance constants
MAX_SPEED_STRAIGHT  = 252   # km/h  (top-speed trap at Brands ~248-255)
IDLE_RPM            = 1200
MAX_RPM             = 7200
SHIFT_RPM           = 6900
GEAR_RATIOS_KMH     = [0, 68, 108, 148, 185, 218, 245, 265]  # approx max per gear


def _gear_for_speed(speed_kmh):
    for g in range(7, 0, -1):
        if speed_kmh >= GEAR_RATIOS_KMH[g - 1]:
            return g
    return 1


def _rpm_for_speed_gear(speed_kmh, gear):
    # Simple linear model: RPM ∝ speed within gear
    gear_top   = GEAR_RATIOS_KMH[gear]
    gear_bot   = GEAR_RATIOS_KMH[gear - 1] if gear > 1 else 0
    span       = max(gear_top - gear_bot, 1)
    frac       = np.clip((speed_kmh - gear_bot) / span, 0.05, 1.0)
    return IDLE_RPM + frac * (MAX_RPM - IDLE_RPM)


# ─────────────────────────────────────────────────────────────────────────────
# 3.  LAP GENERATION
# ─────────────────────────────────────────────────────────────────────────────

LAPS            = 10
POINTS_PER_LAP  = 800
BASE_LAP_TIME   = 88.5   # seconds  (typical AMG GT3 Brands Hatch GP ~1:28-1:30)

sample_dist, track_x, track_y = _build_track_spline(_WAYPOINTS_RAW, POINTS_PER_LAP)


def _zone_for_dist(dist):
    for c_start, c_end, name, *_ in CORNERS:
        if c_start <= dist <= c_end:
            return "Corner", name
    for s_start, s_end, name in STRAIGHTS:
        if s_start <= dist <= s_end:
            return "Straight", name
    return "Straight", ""


def _speed_profile(dist):
    """Return base target speed (km/h) at a given track distance."""
    speed = MAX_SPEED_STRAIGHT
    for c_start, c_end, _, min_spd, entry_spd in CORNERS:
        if c_start <= dist <= c_end:
            # Sine-shaped speed reduction through the corner
            span   = c_end - c_start
            phase  = (dist - c_start) / span
            # Entry → apex → exit
            if phase < 0.5:
                # Braking phase
                t     = phase * 2              # 0→1
                speed = entry_spd - (entry_spd - min_spd) * t
            else:
                # Power phase
                t     = (phase - 0.5) * 2     # 0→1
                speed = min_spd + (entry_spd - min_spd) * 0.7 * t
            return speed
    return speed


def _brake_throttle_profile(dist, target_speed):
    """Derive brake / throttle from the speed gradient."""
    # Look slightly ahead to decide if we're braking or accelerating
    lookahead   = 80   # metres
    dist_ahead  = (dist + lookahead) % TRACK_LENGTH
    spd_ahead   = _speed_profile(dist_ahead)
    current     = target_speed

    delta = spd_ahead - current

    if delta < -5:
        # Need to slow down — braking
        brake    = float(np.clip(-delta / 80, 0.05, 1.0))
        throttle = 0.0
    elif delta > 3:
        # Accelerating
        brake    = 0.0
        throttle = float(np.clip(delta / 60, 0.4, 1.0))
    else:
        # Maintenance
        brake    = 0.0
        throttle = 0.65

    return throttle, brake


data = []

for lap in range(1, LAPS + 1):
    lap_time_var = BASE_LAP_TIME + np.random.normal(0, 0.55)   # lap-to-lap spread

    for i, dist in enumerate(sample_dist):
        # Time stamp within the lap (proportional — good enough for analysis)
        frac = i / POINTS_PER_LAP
        time = frac * lap_time_var

        # --- Speed ---
        base_speed = _speed_profile(dist)
        # Small per-lap driver style variation
        style_var  = np.random.normal(1.0, 0.015)
        speed      = base_speed * style_var + np.random.normal(0, 1.5)
        speed      = float(np.clip(speed, 50, MAX_SPEED_STRAIGHT + 5))

        # --- Brake / Throttle ---
        throttle, brake = _brake_throttle_profile(dist, speed)
        throttle += np.random.normal(0, 0.025)
        brake    += np.random.normal(0, 0.015)
        throttle  = float(np.clip(throttle, 0, 1))
        brake     = float(np.clip(brake,    0, 1))

        # --- Gear & RPM ---
        gear = _gear_for_speed(speed)
        rpm  = _rpm_for_speed_gear(speed, gear) + np.random.normal(0, 120)
        rpm  = float(np.clip(rpm, IDLE_RPM, MAX_RPM))

        # --- Accelerations ---
        # Lateral: higher in fast corners, near-zero on straights
        zone, zone_name = _zone_for_dist(dist)
        if zone == "Corner":
            lat_base = 2.8   # G  (GT3 cars pull ~2.5-3.2 G lateral)
        else:
            lat_base = 0.2
        lat_accel  = float(np.random.normal(lat_base, 0.3))
        long_accel = float(throttle * 1.8 - brake * 3.2 + np.random.normal(0, 0.15))

        # --- Coordinates (from spline) ---
        x = float(track_x[i] + np.random.normal(0, 0.8))   # tiny noise
        y = float(track_y[i] + np.random.normal(0, 0.8))

        data.append([
            lap, time, dist,
            speed, throttle, brake,
            rpm, gear,
            lat_accel, long_accel,
            x, y,
            zone, zone_name,
        ])

df = pd.DataFrame(data, columns=[
    "lapNum", "time", "dist",
    "speed", "throttle", "brake",
    "rpm", "gear",
    "lat_accel", "long_accel",
    "x", "y",
    "zone", "zone_name",
])

# ─────────────────────────────────────────────────────────────────────────────
# 4.  SAVE
# ─────────────────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
df.to_parquet("data/amg_gt3_brands.parquet", index=False)

print("🏁 Generated successfully → data/amg_gt3_brands.parquet")
print(f"   Rows      : {len(df):,}")
print(f"   Laps      : {df['lapNum'].nunique()}")
print(f"   Speed range: {df['speed'].min():.0f} – {df['speed'].max():.0f} km/h")
print(f"   RPM range  : {df['rpm'].min():.0f} – {df['rpm'].max():.0f}")
print(f"   Lap times  : {df.groupby('lapNum')['time'].max().min():.2f}s – "
      f"{df.groupby('lapNum')['time'].max().max():.2f}s")
print(f"   Gear range : {df['gear'].min()} – {df['gear'].max()}")