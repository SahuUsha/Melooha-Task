
from datetime import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
        # 1. Resolve birthplace and detect timezone.
        location_data = get_coordinates(request.birth_place)

        latitude = location_data["latitude"]
        longitude = location_data["longitude"]
        timezone_name = location_data["timezone_name"]

        # 2. Get the birthplace timezone.
        try:
            birth_timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            raise ValueError(
                f"Invalid timezone: {timezone_name}"
            )

        # 3. Interpret the entered time as local birth time.
        birth_datetime_local = request.birth_datetime.replace(
            tzinfo=birth_timezone
        )

        # 4. Convert local birth time to UTC.
        birth_datetime_utc = birth_datetime_local.astimezone(
            timezone.utc
        )

        # 5. Calculate the birth chart.
        chart = calculate_birth_chart(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
        )

        # 6. Save birth details.
        user.birth_datetime = birth_datetime_utc
        user.birth_place = request.birth_place
        user.timezone_name = timezone_name

        # 7. Save chart facts.
        saved_facts = save_chart_facts(
            db=db,
            user_id=request.user_id,
            chart=chart,
        )

        db.commit()

        return {
            "message": "Birth chart calculated successfully.",
            "user_id": request.user_id,
            "birth_place": request.birth_place,
            "resolved_address": location_data["resolved_address"],
            "latitude": latitude,
            "longitude": longitude,
            "timezone_name": timezone_name,
            "birth_datetime_local": birth_datetime_local.isoformat(),
            "birth_datetime_utc": birth_datetime_utc.isoformat(),
            "saved_facts": saved_facts,
            "chart": chart,
        }

    except ValueError as error:
        db.rollback()
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
            detail="User not found.",
        )

    return {
        "user_id": user.id,
        "question_balance": user.question_balance,
    }
