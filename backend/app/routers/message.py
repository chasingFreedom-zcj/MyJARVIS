from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import conversation as conversation_crud
from app.crud import message as message_crud
from app.db.session import get_database
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(
    prefix="/conversation/{conversation_id}/messages",
    tags=["Messages"],
)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    conversation_id: int,
    data: MessageCreate,
    db: AsyncSession = Depends(get_database),
):
    conversation = await conversation_crud.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )

    return await message_crud.create_message(db, conversation, data)


@router.get("", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_database),
):
    conversation = await conversation_crud.get_conversation(db, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )

    return await message_crud.get_messages(
        db,
        conversation_id,
        skip=skip,
        limit=limit,
    )
