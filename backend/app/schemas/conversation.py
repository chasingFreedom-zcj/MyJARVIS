from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ConversationCreate(BaseModel):
    title:str = Field(default="新对话", min_length=1, max_length=100)

class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

class ConversationListResponse(BaseModel):
    total: int
    items: list[ConversationResponse]