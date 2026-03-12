from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem, Note, Project
from ..schemas import ProjectCreate, ProjectDetailRead, ProjectPatch, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])

ALLOWED_SORT_FIELDS = {
    "id": Project.id,
    "name": Project.name,
    "created_at": Project.created_at,
    "updated_at": Project.updated_at,
}


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


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


@router.get("/", response_model=list[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("-created_at", description="Sort by field, prefix with - for desc"),
) -> list[ProjectRead]:
    stmt = select(Project)
    if q:
        stmt = stmt.where(Project.name.contains(q))

    stmt = stmt.order_by(_resolve_sort(sort))

    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return [ProjectRead.model_validate(row) for row in rows]


@router.post("/", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    existing = db.execute(select(Project).where(Project.name == payload.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Project with this name already exists")

    project = Project(name=payload.name, description=payload.description)
    db.add(project)
    db.flush()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetailRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectDetailRead:
    project = _get_project_or_404(db, project_id)
    return ProjectDetailRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def patch_project(
    project_id: int,
    payload: ProjectPatch,
    db: Session = Depends(get_db),
) -> ProjectRead:
    project = _get_project_or_404(db, project_id)
    if payload.name is not None:
        existing = db.execute(select(Project).where(Project.name == payload.name)).scalar_one_or_none()
        if existing and existing.id != project_id:
            raise HTTPException(status_code=409, detail="Project with this name already exists")
        project.name = payload.name

    if "description" in payload.model_fields_set:
        project.description = payload.description

    db.add(project)
    db.flush()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = _get_project_or_404(db, project_id)

    notes = db.execute(select(Note).where(Note.project_id == project_id)).scalars().all()
    for note in notes:
        note.project_id = None
        db.add(note)

    action_items = db.execute(select(ActionItem).where(ActionItem.project_id == project_id)).scalars().all()
    for item in action_items:
        item.project_id = None
        db.add(item)

    db.delete(project)
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
