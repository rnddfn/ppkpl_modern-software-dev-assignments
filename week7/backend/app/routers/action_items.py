from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem, Project
from ..schemas import ActionItemCreate, ActionItemPatch, ActionItemRead

router = APIRouter(prefix="/action-items", tags=["action_items"])

ALLOWED_SORT_FIELDS = {
    "id": ActionItem.id,
    "description": ActionItem.description,
    "completed": ActionItem.completed,
    "created_at": ActionItem.created_at,
    "updated_at": ActionItem.updated_at,
}


def _get_item_or_404(db: Session, item_id: int) -> ActionItem:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


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


@router.get("/", response_model=list[ActionItemRead])
def list_items(
    db: Session = Depends(get_db),
    completed: Optional[bool] = None,
    project_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("-created_at"),
) -> list[ActionItemRead]:
    stmt = select(ActionItem)
    if completed is not None:
        stmt = stmt.where(ActionItem.completed.is_(completed))
    if project_id is not None:
        stmt = stmt.where(ActionItem.project_id == project_id)

    stmt = stmt.order_by(_resolve_sort(sort))

    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return [ActionItemRead.model_validate(row) for row in rows]


@router.post("/", response_model=ActionItemRead, status_code=201)
def create_item(payload: ActionItemCreate, db: Session = Depends(get_db)) -> ActionItemRead:
    if payload.project_id is not None:
        _require_project_exists(db, payload.project_id)

    item = ActionItem(
        description=payload.description,
        completed=False,
        project_id=payload.project_id,
    )
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.put("/{item_id}/complete", response_model=ActionItemRead)
def complete_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = _get_item_or_404(db, item_id)
    item.completed = True
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.put("/{item_id}/reopen", response_model=ActionItemRead)
def reopen_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = _get_item_or_404(db, item_id)
    item.completed = False
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.get("/{item_id}", response_model=ActionItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = _get_item_or_404(db, item_id)
    return ActionItemRead.model_validate(item)


@router.patch("/{item_id}", response_model=ActionItemRead)
def patch_item(item_id: int, payload: ActionItemPatch, db: Session = Depends(get_db)) -> ActionItemRead:
    item = _get_item_or_404(db, item_id)
    if payload.description is not None:
        item.description = payload.description
    if payload.completed is not None:
        item.completed = payload.completed
    if "project_id" in payload.model_fields_set:
        if payload.project_id is not None:
            _require_project_exists(db, payload.project_id)
        item.project_id = payload.project_id
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> Response:
    item = _get_item_or_404(db, item_id)
    db.delete(item)
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


