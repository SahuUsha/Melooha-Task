
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.services.chart_service import calculate_birth_chart
from app.services.chart_storage_service import save_chart_facts
from app.models.chart_fact import ChartFact


def main():
    db = SessionLocal()

    try:
        chart = calculate_birth_chart(
            birth_datetime_utc=datetime(
                2003, 8, 15, 6, 30,
                tzinfo=timezone.utc,
            ),
            latitude=21.1458,
            longitude=79.0882,
        )

        saved_count = save_chart_facts(
            db=db,
            user_id=1,
            chart=chart,
        )

        print(f"\nSuccessfully saved {saved_count} chart facts!")

        saved_facts = (
            db.query(ChartFact)
            .filter(ChartFact.user_id == 1)
            .order_by(ChartFact.fact_key)
            .all()
        )

        print("\nSaved chart facts:")

        for fact in saved_facts:
            print(f"{fact.fact_key}: {fact.fact_value}")

        print(f"\nTotal records: {len(saved_facts)}")

    except Exception as error:
        db.rollback()
        print("Chart storage failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()
