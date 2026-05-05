def generate_insights(df):
    insights = []

    avg_brake = df["brake"].mean()
    avg_throttle = df["throttle"].mean()
    rpm_std = df["rpm"].std()

    # Brake behaviour
    if avg_brake > 0.4:
        insights.append("⚠️ High braking detected — possible time loss in corners")

    if avg_brake < 0.2:
        insights.append("✅ Smooth braking behaviour")

    # Throttle behaviour
    if avg_throttle < 0.6:
        insights.append("⚠️ Low throttle usage — weak acceleration zones")

    if avg_throttle > 0.85:
        insights.append("🔥 Aggressive throttle usage — strong exits")

    # RPM stability
    if rpm_std > df["rpm"].mean() * 0.3:
        insights.append("⚠️ Inconsistent engine load — unstable driving")

    # fallback
    if not insights:
        insights.append("✅ Clean and consistent driving pattern detected")

    return insights