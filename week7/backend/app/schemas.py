from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class NonEmptyPatchModel(StrictBaseModel):
    @model_validator(mode="after")
    def validate_has_updates(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class NoteCreate(StrictBaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)


class NoteRead(StrictBaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotePatch(NonEmptyPatchModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=5000)


class ActionItemCreate(StrictBaseModel):
    description: str = Field(min_length=1, max_length=5000)


class ActionItemRead(StrictBaseModel):
    id: int
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionItemPatch(NonEmptyPatchModel):
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    completed: bool | None = None


