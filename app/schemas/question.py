
from pydantic import BaseModel, Field


class QuestionAskRequest(BaseModel):
    user_id: int = Field(gt=0)
    question: str = Field(
        min_length=3,
        max_length=2000,
    )


class QuestionTopUpRequest(BaseModel):
    user_id: int = Field(gt=0)
    amount: int = Field(
        gt=0,
        le=100,
        description="Number of question credits to add",
    )
