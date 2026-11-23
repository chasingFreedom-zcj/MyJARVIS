from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate


async def create_conversation(
    db: AsyncSession,
    data: ConversationCreate,
) -> Conversation:
    conversation = Conversation(
        title=data.title,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


async def get_conversations(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Conversation], int]:
    count_result = await db.execute(select(func.count()).select_from(Conversation))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
    )

    conversations = list(result.scalars().all())

    return conversations, total


async def get_conversation(
    db: AsyncSession,
    conversation_id: int,
) -> Conversation | None:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))

    return result.scalar_one_or_none()


async def update_conversation(
    db: AsyncSession,
    conversation: Conversation,
    data: ConversationUpdate,
) -> Conversation:
    conversation.title = data.title

    await db.commit()
    await db.refresh(conversation)

    return conversation


async def delete_conversation(
    db: AsyncSession,
    conversation: Conversation,
) -> None:
    await db.delete(conversation)
    await db.commit()
