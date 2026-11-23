from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.message import MessageCreate


async def create_message(
    db: AsyncSession,
    conversation: Conversation,
    data: MessageCreate,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role="user",
        content=data.content,
    )
    db.add(message)

    conversation.updated_at = func.now()

    await db.commit()
    await db.refresh(message)

    return message


async def get_messages(
    db: AsyncSession,
    conversation_id: int,
    skip: int,
    limit: int = 50,
) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .offset(skip)
        .limit(limit)
    )

    return list(result.scalars().all())


async def get_recent_messages(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 20,
) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )

    messages = list(result.scalars().all())
    messages.reverse()

    return messages


async def create_assistant_message(
    db: AsyncSession, conversation: Conversation, content: str
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=content,
    )

    db.add(message)

    conversation.updated_at = func.now()

    await db.commit()
    await db.refresh(message)

    return message
