from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from .. import db
# Import the Pydantic schemas that define the request/response contract.
from ..schemas import NoteCreate, NoteResponse


router = APIRouter(prefix="/notes", tags=["notes"])


# response_model tells FastAPI to validate and serialise the return value
# using NoteResponse, and to document this shape in the OpenAPI schema.
@router.post("", response_model=NoteResponse, status_code=201)
def create_note(body: NoteCreate) -> NoteResponse:
    """Create a new note.  The 'content' field is required and must be non-empty."""
    # NoteCreate already validated that body.content is non-empty (min_length=1).
    note_id = db.insert_note(body.content)
    note = db.get_note(note_id)
    return NoteResponse(id=note["id"], content=note["content"], created_at=note["created_at"])


@router.get("", response_model=List[NoteResponse])
def list_notes() -> List[NoteResponse]:
    """Return all notes in reverse creation order."""
    rows = db.list_notes()
    return [
        NoteResponse(id=r["id"], content=r["content"], created_at=r["created_at"])
        for r in rows
    ]


@router.get("/{note_id}", response_model=NoteResponse)
def get_single_note(note_id: int) -> NoteResponse:
    """Return a single note by its ID, or 404 if it does not exist."""
    row = db.get_note(note_id)
    if row is None:
        raise HTTPException(status_code=404, detail="note not found")
    return NoteResponse(id=row["id"], content=row["content"], created_at=row["created_at"])