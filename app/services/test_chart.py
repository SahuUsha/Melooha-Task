
from datetime import datetime, timezone

from app.services.chart_service import calculate_birth_chart


# Sample test profile
# These are test inputs, not a real user's birth details.

chart = calculate_birth_chart(
    birth_datetime_utc=datetime(
        2003, 8, 15, 6, 30,
        tzinfo=timezone.utc,
    ),
    latitude=21.1458,
    longitude=79.0882,
)

print("\n========== VEDIC BIRTH CHART ==========")

print("\nAscendant:")
print(chart["ascendant"])

print("\nPlanetary Positions:")

for planet, details in chart["planets"].items():
    print(
        f"{planet:10} | "
        f"{details['sign']:12} | "
        f"House: {details['house']:2} | "
        f"Degree: {details['degree_in_sign']:8} | "
        f"Retrograde: {details['retrograde']}"
    )
