import pandas as pd

from src.analysis import (
    prepare_data,
    generate_engine_report,
    get_best_lap
)

# ================================
# LOAD DATA
# ================================

df = pd.read_parquet("data/amg_gt3_brands.parquet")

df = prepare_data(df)

# ================================
# BASIC INFO
# ================================

best_lap = get_best_lap(df)

print("\n🏁 BEST LAP:", best_lap)

# ================================
# ENGINE REPORT
# ================================

report = generate_engine_report(df)

print("\n🧠 ENGINE REPORT:\n")

for r in report:
    print(f"Segment {r['segment']}")
    print(f"Time Loss: -{r['time_loss']}s")
    print(f"Cause: {r['reason']}")
    print("-" * 30)