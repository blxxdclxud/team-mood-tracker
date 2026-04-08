"""ORM models and Pydantic schemas for mood entries."""

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class MoodValue(str, enum.Enum):
    """Enumeration of supported mood values."""

    happy = "happy"
    neutral = "neutral"
    stressed = "stressed"
    sad = "sad"
    excited = "excited"


MOOD_RATING: dict[MoodValue, int] = {
    MoodValue.excited: 5,
    MoodValue.happy: 4,
    MoodValue.neutral: 3,
    MoodValue.sad: 2,
    MoodValue.stressed: 1,
}

MOOD_EMOJI: dict[MoodValue, str] = {
    MoodValue.excited: "🤩",
    MoodValue.happy: "😊",
    MoodValue.neutral: "😐",
    MoodValue.sad: "😢",
    MoodValue.stressed: "😤",
}


class MoodEntry(Base):
    """SQLAlchemy ORM model representing a single mood entry."""

    __tablename__ = "mood_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mood: Mapped[str] = mapped_column(
        Enum(MoodValue, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class MoodEntryCreate(BaseModel):
    """Schema for creating a new mood entry."""

    user: str = Field(..., min_length=1, max_length=64, examples=["alice"])
    mood: MoodValue = Field(..., examples=[MoodValue.happy])
    comment: str = Field("", max_length=500, examples=["Great standup today!"])


class MoodEntryUpdate(BaseModel):
    """Schema for updating an existing mood entry (all fields optional)."""

    mood: MoodValue | None = Field(None, examples=[MoodValue.neutral])
    comment: str | None = Field(None, max_length=500, examples=["Feeling better now."])


class MoodEntryRead(BaseModel):
    """Schema returned when reading a mood entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user: str
    mood: MoodValue
    rating: int
    comment: str
    created_at: datetime


class DailyMoodStat(BaseModel):
    """Aggregate mood statistics for a single day."""

    date: str
    average_rating: float
    entry_count: int


class PeriodMoodStat(BaseModel):
    """Aggregate mood statistics for a requested period."""

    start_date: str
    end_date: str
    average_rating: float
    entry_count: int
    mood_distribution: dict[str, int]


class MoodDistribution(BaseModel):
    """Mood count distribution for a given scope (day or all-time)."""

    scope: str
    distribution: dict[str, int]
