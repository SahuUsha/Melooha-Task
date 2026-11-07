
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    question_balance: int

    model_config = ConfigDict(from_attributes=True)
