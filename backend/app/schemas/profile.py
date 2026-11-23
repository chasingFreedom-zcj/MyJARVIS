from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
class ProfileCreate(BaseModel):
    nickname: str = Field(min_length = 1,max_length = 50)
    age: int|None = Field(default=None, ge=1, le=120)
    gender: str|None = Field(default=None)
    career_stage: str|None = Field(default=None,max_length=50)
    main_goal: str|None = None

class ProfileUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    age: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = Field(default=None)
    career_stage: str | None = Field(default=None, max_length=50)
    main_goal: str | None = None

class ProfileResponse(BaseModel):
    id: int
    nickname: str
    age: int | None
    gender: str | None
    career_stage: str | None
    main_goal: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
