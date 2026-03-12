from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from .. import db
from ..services.extract import extract_action_items, extract_action_items_llm
# Import the Pydantic schemas that define the request/response contract.
from ..schemas import (
    ActionItemOut,
    ActionItemResponse,
    ExtractRequest,
    ExtractResponse,
    MarkDoneRequest,
    MarkDoneResponse,
)


router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post("/extract", response_model=ExtractResponse)
def extract(body: ExtractRequest) -> ExtractResponse:
    """Extract action items from free-form text.

    Set save_note=true in the request body to also persist the note.
    """
    # ExtractRequest validates that body.text is non-empty (min_length=1).
    note_id: Optional[int] = None
    if body.save_note:
        note_id = db.insert_note(body.text)

    items = extract_action_items(body.text)
    ids = db.insert_action_items(items, note_id=note_id)
    return ExtractResponse(
        note_id=note_id,
        items=[ActionItemOut(id=i, text=t) for i, t in zip(ids, items)],
    )


@router.post("/extract-llm", response_model=ExtractResponse)
def extract_llm(body: ExtractRequest) -> ExtractResponse:
    """Extract action items using the Ollama LLM instead of heuristics.

    Accepts the same request body as /extract and returns the same response shape.
    """
    note_id: Optional[int] = None
    if body.save_note:
        note_id = db.insert_note(body.text)

    items = extract_action_items_llm(body.text)
    ids = db.insert_action_items(items, note_id=note_id)
    return ExtractResponse(
        note_id=note_id,
        items=[ActionItemOut(id=i, text=t) for i, t in zip(ids, items)],
    )


@router.get("", response_model=List[ActionItemResponse])
def list_all(note_id: Optional[int] = None) -> List[ActionItemResponse]:
    """Return all action items, optionally filtered by note_id."""
    rows = db.list_action_items(note_id=note_id)
    return [
        ActionItemResponse(
            id=r["id"],
            note_id=r["note_id"],
            text=r["text"],
            done=bool(r["done"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/{action_item_id}/done", response_model=MarkDoneResponse)
def mark_done(action_item_id: int, body: MarkDoneRequest) -> MarkDoneResponse:
    """Mark an action item as done or not done.

    Returns 404 when no action item with the given id exists.
    """
    # db.mark_action_item_done now returns the number of rows updated.
    # A count of 0 means no row matched — the id does not exist.
    updated = db.mark_action_item_done(action_item_id, body.done)
    if updated == 0:
        raise HTTPException(status_code=404, detail="action item not found")
    return MarkDoneResponse(id=action_item_id, done=body.done)


