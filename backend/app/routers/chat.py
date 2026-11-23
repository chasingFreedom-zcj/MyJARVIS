from alembic.command import history
from fastapi import APIRouter, Depends, HTTPException, status
from openai import APIError
from openai.types.beta import assistant
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database
from app.crud import conversation as conversation_crud
from app.crud import message as message_crud
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.chat import ChatResponse
from app.services.llm import generate_reply

router = APIRouter(
    prefix="/conversations",
    tags=["Chat"],
)

@router.post(
    "/{conversation_id}/chat",
    response_model=ChatResponse,
)
async def create_chat(
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

    user_message = await message_crud.create_message(db, conversation, data)

    history = await message_crud.get_recent_messages(
        db,
        conversation_id,
        limit=20,
    )

    messages = [
        {
            "role": item.role,
            "content": item.content,
        }
        for item in history
    ]

    try:
        reply = await generate_reply(messages)
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="大模型API调用失败，请检查API配置或稍后再试"
        )from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    assistant_message = (
        await message_crud.create_assistant_message(db, conversation, reply)
    )

    return ChatResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
    )