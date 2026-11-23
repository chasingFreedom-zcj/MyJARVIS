from datetime import datetime
from sqlalchemy import String, Text, DateTime, true, DropTable
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nickname: Mapped[int] = mapped_column(
        String(50),
        index=False,
    )
    age: Mapped[int|None] = mapped_column(nullable=true)
    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )
    career_stage: Mapped[str|None] = mapped_column(
        String(50),
        nullable = True,
    )
    main_goal: Mapped[str|None] = mapped_column(
        Text,
        nullable = True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        nullable = False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        onupdate=datetime.now(),
        nullable = False,
    )