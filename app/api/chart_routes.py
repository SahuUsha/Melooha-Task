
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.chart import ChartCalculateRequest
from app.services.chart_service import calculate_birth_chart
from app.services.chart_storage_service import save_chart_facts
from app.services.geocoding_service import get_coordinates


router = APIRouter(prefix="/chart", tags=["Birth Chart"])


@router.post("/calculate")
def calculate_chart(
    request: ChartCalculateRequest,
    db: Session = Depends(get_db),
):
    # 1. Verify that the user exists.
    user = (
        db.query(User)
        .filter(User.id == request.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    try:
        # 2. Convert birth location into coordinates.
        location_data = get_coordinates(request.birth_place)

        latitude = location_data["latitude"]
        longitude = location_data["longitude"]

        # 3. Convert birth datetime to UTC.
        birth_datetime_utc = request.birth_datetime.astimezone(
            timezone.utc
        )

        # 4. Calculate the Vedic birth chart.
        chart = calculate_birth_chart(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
        )

        # 5. Save calculated facts in PostgreSQL.
        saved_facts = save_chart_facts(
            db=db,
            user_id=request.user_id,
            chart=chart,
        )

        # 6. Return chart and resolved location.
        return {
            "message": "Birth chart calculated successfully.",
            "user_id": request.user_id,
            "birth_place": request.birth_place,
            "resolved_address": location_data["resolved_address"],
            "latitude": latitude,
            "longitude": longitude,
            "saved_facts": saved_facts,
            "chart": chart,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        db.rollback()
        print(f"Birth chart calculation failed: {error}")

        raise HTTPException(
            status_code=500,
            detail="Failed to calculate birth chart.",
        )



@router.get("/{user_id}/balance")
def get_question_balance(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return {
        "user_id": user.id,
        "question_balance": user.question_balance,
    }
