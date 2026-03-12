"""
Pydantic models that define the request and response shapes for every endpoint.

Having explicit schemas here means:
- FastAPI validates incoming JSON automatically and returns a clear 422 on bad input.
- The generated OpenAPI docs show real field names and types instead of empty objects.
- Response bodies are type-checked at serialization time.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


class NoteCreate(BaseModel):
    """Request body for POST /notes."""

    # "content" matches the column name in the notes table.
    content: str = Field(..., min_length=1, description="Free-form text of the note")


class NoteResponse(BaseModel):
    """Response shape for a single note (create, get, list)."""

    id: int
    content: str
    # SQLite stores timestamps as plain strings ("YYYY-MM-DD HH:MM:SS").
    # Keeping it as str avoids timezone-parsing surprises while still being explicit.
    created_at: str


# ---------------------------------------------------------------------------
# Action Items
# ---------------------------------------------------------------------------


class ActionItemOut(BaseModel):
    """Minimal action item representation used inside ExtractResponse."""

    id: int
    text: str


class ExtractRequest(BaseModel):
    """Request body for POST /action-items/extract."""

    text: str = Field(..., min_length=1, description="Note text to extract action items from")
    # When True the note text is also saved to the notes table.
    save_note: bool = Field(False, description="Also persist the note to the database")


class ExtractResponse(BaseModel):
    """Response body for POST /action-items/extract."""

    # None when save_note was False.
    note_id: Optional[int] = None
    items: List[ActionItemOut]


class ActionItemResponse(BaseModel):
    """Full action item record returned by GET /action-items."""

    id: int
    note_id: Optional[int] = None
    text: str
    done: bool
    created_at: str


class MarkDoneRequest(BaseModel):
    """Request body for POST /action-items/{id}/done."""

    # Defaults to True so callers can POST an empty body to mark as done.
    done: bool = Field(True, description="True to mark done, False to unmark")


class MarkDoneResponse(BaseModel):
    """Response body for POST /action-items/{id}/done."""

    id: int
    done: bool
