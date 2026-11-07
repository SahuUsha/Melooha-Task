
from datetime import datetime

from pydantic import BaseModel, Field


class ChartCalculateRequest(BaseModel):
    user_id: int = Field(gt=0)

    # Local birth date and time entered by the user.
    # The backend detects the timezone from the birthplace.
    birth_datetime: datetime

    birth_place: str = Field(
        min_length=3,
        max_length=200
    )
