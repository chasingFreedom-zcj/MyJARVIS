from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import conversation as conversation_crud
from app.db.session import get_database
from app.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_database),
):
    return await conversation_crud.create_conversation(db, data)


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_database),
):
    conversations, total = await conversation_crud.get_conversations(db, skip=skip, limit=limit)

    return {
        "total": total,
        "items": conversations,
    }


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_database),
):
    conversation = await conversation_crud.get_conversation(db, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    return conversation


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_database),
):
    conversation = await conversation_crud.get_conversation(db, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )
    return await conversation_crud.update_conversation(db, conversation, data)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_database),
):
    conversation = await conversation_crud.get_conversation(db, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )

    await conversation_crud.delete_conversation(db, conversation)
