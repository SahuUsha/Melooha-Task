
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ChartCalculateRequest(BaseModel):
    user_id: int = Field(gt=0)

    # Must include a timezone offset, e.g. +05:30 for India.
    birth_datetime: datetime

    birth_place: str = Field(min_length=3, max_length=200)

    @field_validator("birth_datetime")
    @classmethod
    def validate_birth_datetime(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Birth datetime must include a timezone offset."
            )

        return value
