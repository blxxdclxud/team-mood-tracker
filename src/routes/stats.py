"""Statistics and analytics API routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src import crud
from src.database import get_db
from src.models import DailyMoodStat, MoodDistribution, PeriodMoodStat

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/daily",
    response_model=list[DailyMoodStat],
    summary="Daily mood trends",
    description=(
        "Return per-day average mood rating and entry count for the last N days. "
        "Useful for plotting historical mood changes over time."
    ),
    responses={
        200: {
            "description": "List of daily mood statistics",
            "content": {
                "application/json": {
                    "example": [
                        {"date": "2024-01-14", "average_rating": 3.5, "entry_count": 4},
                        {"date": "2024-01-15", "average_rating": 4.0, "entry_count": 5},
                    ]
                }
            },
        }
    },
)
def daily_trends(
    days: int = Query(30, ge=1, le=365, description="Number of past days to include"),
    db: Session = Depends(get_db),
) -> list[DailyMoodStat]:
    """Return daily average mood ratings for the requested window."""
    return crud.get_daily_stats(db, days=days)


@router.get(
    "/aggregate",
    response_model=PeriodMoodStat,
    summary="Aggregate mood statistics for a period",
    description=(
        "Compute aggregate mood statistics (average rating, entry count, "
        "mood distribution) for entries within a specified date range."
    ),
    responses={
        200: {
            "description": "Aggregate statistics for the requested period",
            "content": {
                "application/json": {
                    "example": {
                        "start_date": "2024-01-01",
                        "end_date": "2024-01-31",
                        "average_rating": 3.7,
                        "entry_count": 42,
                        "mood_distribution": {
                            "happy": 15,
                            "neutral": 12,
                            "stressed": 8,
                            "sad": 4,
                            "excited": 3,
                        },
                    }
                }
            },
        }
    },
)
def aggregate_stats(
    start_date: date = Query(..., description="Start of the period (inclusive)"),
    end_date: date = Query(..., description="End of the period (inclusive)"),
    db: Session = Depends(get_db),
) -> PeriodMoodStat:
    """Compute and return aggregate mood stats for a date range."""
    return crud.get_period_stats(db, start_date, end_date)


@router.get(
    "/distribution",
    response_model=MoodDistribution,
    summary="Mood distribution for barplots",
    description=(
        "Return mood counts suitable for rendering barplots. "
        "If `target_date` is provided, counts are limited to that day; "
        "otherwise all-time data is returned."
    ),
    responses={
        200: {
            "description": "Mood distribution counts",
            "content": {
                "application/json": {
                    "example": {
                        "scope": "2024-01-15",
                        "distribution": {
                            "happy": 3,
                            "neutral": 2,
                            "stressed": 1,
                            "sad": 0,
                            "excited": 1,
                        },
                    }
                }
            },
        }
    },
)
def mood_distribution(
    target_date: date | None = Query(
        None, description="Specific date to filter by; omit for all-time"
    ),
    db: Session = Depends(get_db),
) -> MoodDistribution:
    """Return mood distribution counts, scoped to a day or all-time."""
    return crud.get_mood_distribution(db, target_date=target_date)
