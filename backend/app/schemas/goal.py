from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str|None = None

    category: str = Field(default="学习", max_length = 100)
    priority:Literal["low", "medium", "high"] = "medium"
    status: Literal["not_satrted", "in_progress", "completed"] = "not_satrted"

    progress: int = Field(default=0,ge=0,le=100)

    start_date: date|None = None
    deadline: date|None = None

    @model_validator(mode = "after")
    def validate_dates(self):
        if(
            self.start_date is not None
            and self.deadline is not None
            and self.start_date > self.deadline
        ):
            raise ValueError("截止日期不能早于开始日期")
        return self

class GoalUpdate(BaseModel):
    title: str|None = Field(default=None, min_length=1, max_length=100)
    description: str|None = None

    category: str|None = Field(default=None, max_length=30)
    priority: Literal["low", "medium", "high"] | None = None
    status:Literal["not_satrted", "in_progress", "completed"]|None = None

    progress: int|None = Field(default=0,ge=0,le=100)

    start_date: date|None = None
    deadline: date|None = None

    @model_validator(mode = "after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.deadline is not None
            and self.deadline < self.start_date
        ):
            raise ValueError("截止日期不能早于开始日期")
        return self

class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    title:str
    description:str|None
    category: str
    priority: str
    status: str
    progress:int
    start_date: date|None
    deadline:date|None
    created_at:datetime|None
    updated_at:datetime|None