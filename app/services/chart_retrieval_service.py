
from sqlalchemy.orm import Session

from app.models.chart_fact import ChartFact


def get_user_chart_facts(
    db: Session,
    user_id: int,
) -> list[dict]:
    """Retrieve calculated birth-chart facts for a user."""

    facts = (
        db.query(ChartFact)
        .filter(ChartFact.user_id == user_id)
        .order_by(ChartFact.id.asc())
        .all()
    )

    return [
        {
            "fact_key": fact.fact_key,
            "fact_value": fact.fact_value,
            "source": fact.source,
        }
        for fact in facts
    ]
