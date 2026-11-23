from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,nullable=False,default=1
    )

    title: Mapped[str] = mapped_column(
        String(200),nullable=False,default="新对话"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,nullable=False,server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    messages: Mapped[list] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )