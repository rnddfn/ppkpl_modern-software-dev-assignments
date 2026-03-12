from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note, Project
from ..schemas import NoteCreate, NotePatch, NoteRead

router = APIRouter(prefix="/notes", tags=["notes"])

ALLOWED_SORT_FIELDS = {
    "id": Note.id,
    "title": Note.title,
    "content": Note.content,
    "created_at": Note.created_at,
    "updated_at": Note.updated_at,
}


def _get_note_or_404(db: Session, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


def _resolve_sort(sort: str):
    sort_field = sort.lstrip("-")
    sort_column = ALLOWED_SORT_FIELDS.get(sort_field)
    if sort_column is None:
        allowed = ", ".join(ALLOWED_SORT_FIELDS)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field '{sort_field}'. Allowed values: {allowed}",
        )
    order_fn = desc if sort.startswith("-") else asc
    return order_fn(sort_column)


def _require_project_exists(db: Session, project_id: int) -> None:
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/", response_model=list[NoteRead])
def list_notes(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    project_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("-created_at", description="Sort by field, prefix with - for desc"),
) -> list[NoteRead]:
    stmt = select(Note)
    if q:
        stmt = stmt.where((Note.title.contains(q)) | (Note.content.contains(q)))
    if project_id is not None:
        stmt = stmt.where(Note.project_id == project_id)

    stmt = stmt.order_by(_resolve_sort(sort))

    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return [NoteRead.model_validate(row) for row in rows]


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    if payload.project_id is not None:
        _require_project_exists(db, payload.project_id)

    note = Note(title=payload.title, content=payload.content, project_id=payload.project_id)
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.patch("/{note_id}", response_model=NoteRead)
def patch_note(note_id: int, payload: NotePatch, db: Session = Depends(get_db)) -> NoteRead:
    note = _get_note_or_404(db, note_id)
    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    if "project_id" in payload.model_fields_set:
        if payload.project_id is not None:
            _require_project_exists(db, payload.project_id)
        note.project_id = payload.project_id
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> Response:
    note = _get_note_or_404(db, note_id)
    db.delete(note)
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = _get_note_or_404(db, note_id)
    return NoteRead.model_validate(note)


