"""CRUD operations for mood entries."""

from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from src.models import (
    MOOD_RATING,
    DailyMoodStat,
    MoodDistribution,
    MoodEntry,
    MoodEntryCreate,
    MoodEntryUpdate,
    MoodValue,
    PeriodMoodStat,
)


def _day_start(d: date) -> datetime:
    """Return midnight UTC for the given date."""
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _day_end(d: date) -> datetime:
    """Return 23:59:59 UTC for the given date."""
    return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)


def _apply_date_filters(
    query: "Query[MoodEntry]",
    start_date: date | None,
    end_date: date | None,
) -> "Query[MoodEntry]":
    """Narrow a query by start and end date bounds when provided."""
    if start_date:
        query = query.filter(MoodEntry.created_at >= _day_start(start_date))
    if end_date:
        query = query.filter(MoodEntry.created_at <= _day_end(end_date))
    return query


def _count_distribution(entries: list[MoodEntry]) -> dict[str, int]:
    """Tally mood occurrences across a list of entries."""
    distribution: dict[str, int] = {m.value: 0 for m in MoodValue}
    for e in entries:
        distribution[e.mood] = distribution.get(e.mood, 0) + 1
    return distribution


def create_mood_entry(db: Session, payload: MoodEntryCreate) -> MoodEntry:
    """Persist a new mood entry and return the created ORM instance."""
    entry = MoodEntry(
        user=payload.user,
        mood=payload.mood.value,
        rating=MOOD_RATING[payload.mood],
        comment=payload.comment,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_mood_entry(db: Session, entry_id: int) -> MoodEntry | None:
    """Return a single mood entry by primary key, or None if not found."""
    return db.query(MoodEntry).filter(MoodEntry.id == entry_id).first()


def get_mood_entries(
    db: Session,
    user: str | None = None,
    mood: MoodValue | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[MoodEntry]:
    """Return a paginated list of mood entries with optional filters."""
    query = db.query(MoodEntry)
    if user:
        query = query.filter(MoodEntry.user == user)
    if mood:
        query = query.filter(MoodEntry.mood == mood.value)
    query = _apply_date_filters(query, start_date, end_date)
    return query.order_by(MoodEntry.created_at.desc()).offset(skip).limit(limit).all()


def update_mood_entry(
    db: Session, entry_id: int, payload: MoodEntryUpdate
) -> MoodEntry | None:
    """Update a mood entry's mood and/or comment; return updated instance or None."""
    entry = get_mood_entry(db, entry_id)
    if entry is None:
        return None
    if payload.mood is not None:
        entry.mood = payload.mood.value
        entry.rating = MOOD_RATING[payload.mood]
    if payload.comment is not None:
        entry.comment = payload.comment
    db.commit()
    db.refresh(entry)
    return entry


def delete_mood_entry(db: Session, entry_id: int) -> bool:
    """Delete a mood entry by id; return True on success, False if not found."""
    entry = get_mood_entry(db, entry_id)
    if entry is None:
        return False
    db.delete(entry)
    db.commit()
    return True


def get_daily_stats(db: Session, days: int = 30) -> list[DailyMoodStat]:
    """Return per-day average rating and entry count for the last N days."""
    rows = (
        db.query(
            func.date(MoodEntry.created_at).label("date"),
            func.avg(MoodEntry.rating).label("avg_rating"),
            func.count(MoodEntry.id).label("count"),
        )
        .group_by(func.date(MoodEntry.created_at))
        .order_by(func.date(MoodEntry.created_at))
        .limit(days)
        .all()
    )
    return [
        DailyMoodStat(
            date=str(row.date),
            average_rating=round(float(row.avg_rating), 2),
            entry_count=int(row.count),
        )
        for row in rows
    ]


def get_period_stats(db: Session, start_date: date, end_date: date) -> PeriodMoodStat:
    """Return aggregate mood statistics for entries within the given date range."""
    entries = (
        db.query(MoodEntry)
        .filter(
            MoodEntry.created_at >= _day_start(start_date),
            MoodEntry.created_at <= _day_end(end_date),
        )
        .all()
    )
    count = len(entries)
    avg_rating = round(sum(e.rating for e in entries) / count, 2) if count else 0.0
    return PeriodMoodStat(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        average_rating=avg_rating,
        entry_count=count,
        mood_distribution=_count_distribution(entries),
    )


def get_mood_distribution(
    db: Session, target_date: date | None = None
) -> MoodDistribution:
    """Return mood distribution counts, optionally filtered to a single day."""
    query = db.query(MoodEntry)
    if target_date:
        query = query.filter(
            MoodEntry.created_at >= _day_start(target_date),
            MoodEntry.created_at <= _day_end(target_date),
        )
        scope = target_date.isoformat()
    else:
        scope = "all-time"
    return MoodDistribution(scope=scope, distribution=_count_distribution(query.all()))
