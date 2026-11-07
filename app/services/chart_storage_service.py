
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chart_fact import ChartFact


CHART_SOURCE = "swiss_ephemeris_lahiri_whole_sign"


def save_chart_facts(
    db: Session,
    user_id: int,
    chart: dict,
) -> int:
    """Save calculated birth-chart facts for a user."""

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise ValueError(f"User with ID {user_id} does not exist")

    facts = []

    def add_fact(key: str, value):
        facts.append(
            ChartFact(
                user_id=user_id,
                fact_key=key,
                fact_value=str(value),
                source=CHART_SOURCE,
            )
        )

    # Calculation metadata
    add_fact("calculation_system", chart["calculation_system"])
    add_fact("ayanamsha", chart["ayanamsha"])
    add_fact("house_system", chart["house_system"])

    # Ascendant facts
    ascendant = chart["ascendant"]

    add_fact("ascendant.sign", ascendant["sign"])
    add_fact("ascendant.longitude", ascendant["longitude"])
    add_fact("ascendant.degree", ascendant["degree_in_sign"])

    # Planetary facts
    for planet_name, details in chart["planets"].items():
        prefix = planet_name.lower()

        add_fact(f"{prefix}.sign", details["sign"])
        add_fact(f"{prefix}.longitude", details["longitude"])
        add_fact(f"{prefix}.degree", details["degree_in_sign"])
        add_fact(f"{prefix}.house", details["house"])
        add_fact(f"{prefix}.retrograde", details["retrograde"])

    try:
        # Replace the previous calculated chart for this user.
        db.query(ChartFact).filter(
            ChartFact.user_id == user_id,
            ChartFact.source == CHART_SOURCE,
        ).delete(synchronize_session=False)

        db.add_all(facts)
        db.commit()

        return len(facts)

    except Exception:
        db.rollback()
        raise
