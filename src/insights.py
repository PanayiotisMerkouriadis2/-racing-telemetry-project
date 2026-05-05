def generate_insights(df):
    insights = []

    avg_brake = df["brake"].mean()
    avg_throttle = df["throttle"].mean()
    avg_rpm = df["rpm"].mean()

    # Brake behaviour
    if avg_brake > 0.4:
        insights.append("⚠️ High braking detected (possible over-braking)")

    if avg_brake < 0.2:
        insights.append("✅ Smooth braking behaviour")

    # Throttle behaviour
    if avg_throttle < 0.6:
        insights.append("⚠️ Low throttle usage (poor acceleration zones)")

    if avg_throttle > 0.85:
        insights.append("🔥 Aggressive throttle usage (strong exit performance)")

    # RPM behaviour
    if avg_rpm < df["rpm"].mean():
        insights.append("⚠️ RPM efficiency below dataset average")

    return insights