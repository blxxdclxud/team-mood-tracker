"""CRUD API routes for mood entries."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src import crud
from src.database import get_db
from src.models import MoodEntryCreate, MoodEntryRead, MoodEntryUpdate, MoodValue

router = APIRouter(prefix="/moods", tags=["moods"])


@router.post(
    "/",
    response_model=MoodEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a mood entry",
    description=(
        "Create a new mood entry for a team member. "
        "The rating is derived automatically from the chosen mood. "
        "No authentication is required — the `user` field identifies the submitter."
    ),
    responses={
        201: {
            "description": "Mood entry created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user": "alice",
                        "mood": "happy",
                        "rating": 4,
                        "comment": "Great standup today!",
                        "created_at": "2024-01-15T09:30:00Z",
                    }
                }
            },
        }
    },
)
def create_entry(
    payload: MoodEntryCreate, db: Session = Depends(get_db)
) -> MoodEntryRead:
    """Create and persist a new mood entry."""
    entry = crud.create_mood_entry(db, payload)
    return MoodEntryRead.model_validate(entry)


@router.get(
    "/",
    response_model=list[MoodEntryRead],
    summary="List mood entries",
    description=(
        "Retrieve a paginated list of mood entries. "
        "Optionally filter by `user`, `mood`, `start_date`, and `end_date`."
    ),
    responses={
        200: {
            "description": "List of mood entries",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "user": "alice",
                            "mood": "happy",
                            "rating": 4,
                            "comment": "Great standup!",
                            "created_at": "2024-01-15T09:30:00Z",
                        }
                    ]
                }
            },
        }
    },
)
def list_entries(
    user: str | None = Query(None, description="Filter by username"),
    mood: MoodValue | None = Query(None, description="Filter by mood value"),
    start_date: date | None = Query(
        None, description="Include entries on or after this date"
    ),
    end_date: date | None = Query(
        None, description="Include entries on or before this date"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> list[MoodEntryRead]:
    """Return a filtered, paginated list of mood entries."""
    entries = crud.get_mood_entries(
        db,
        user=user,
        mood=mood,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return [MoodEntryRead.model_validate(e) for e in entries]


@router.get(
    "/{entry_id}",
    response_model=MoodEntryRead,
    summary="Get a single mood entry",
    description="Retrieve one mood entry by its unique identifier.",
    responses={
        200: {
            "description": "The requested mood entry",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user": "alice",
                        "mood": "happy",
                        "rating": 4,
                        "comment": "Great standup!",
                        "created_at": "2024-01-15T09:30:00Z",
                    }
                }
            },
        },
        404: {"description": "Mood entry not found"},
    },
)
def get_entry(entry_id: int, db: Session = Depends(get_db)) -> MoodEntryRead:
    """Fetch a mood entry by id, raising 404 if absent."""
    entry = crud.get_mood_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Mood entry not found")
    return MoodEntryRead.model_validate(entry)


@router.put(
    "/{entry_id}",
    response_model=MoodEntryRead,
    summary="Update a mood entry",
    description=(
        "Partially update an existing mood entry. "
        "Only the fields provided in the request body are changed."
    ),
    responses={
        200: {
            "description": "Updated mood entry",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user": "alice",
                        "mood": "neutral",
                        "rating": 3,
                        "comment": "Feeling better now.",
                        "created_at": "2024-01-15T09:30:00Z",
                    }
                }
            },
        },
        404: {"description": "Mood entry not found"},
    },
)
def update_entry(
    entry_id: int, payload: MoodEntryUpdate, db: Session = Depends(get_db)
) -> MoodEntryRead:
    """Update mood and/or comment of an existing entry."""
    entry = crud.update_mood_entry(db, entry_id, payload)
    if entry is None:
        raise HTTPException(status_code=404, detail="Mood entry not found")
    return MoodEntryRead.model_validate(entry)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a mood entry",
    description="Permanently remove a mood entry by its id.",
    responses={
        204: {"description": "Mood entry deleted"},
        404: {"description": "Mood entry not found"},
    },
)
def delete_entry(entry_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a mood entry, raising 404 if it does not exist."""
    deleted = crud.delete_mood_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mood entry not found")
