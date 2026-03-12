# Week 2 - Action Item Extractor

A beginner-friendly FastAPI + SQLite app for turning meeting notes into actionable tasks.

## What This Project Does

This Week 2 app lets you:

- paste free-form notes in a simple web UI
- extract action items from the notes
- optionally save the note to a SQLite database
- save extracted action items to the database
- mark action items as done
- list saved notes

The app includes both:

- `Extract` flow
- `Extract LLM` flow

Both flows currently use Ollama-backed extraction logic from `week2/app/services/extract.py`.

## Project Structure

- `app/main.py` - FastAPI entry point and app setup
- `app/routers/notes.py` - notes endpoints
- `app/routers/action_items.py` - action item endpoints
- `app/services/extract.py` - LLM extraction service (Ollama)
- `app/db.py` - SQLite schema and data access helpers
- `app/schemas.py` - Pydantic request/response models
- `frontend/index.html` - minimal frontend UI
- `tests/test_extract.py` - extraction unit tests
- `assignment.md` - assignment instructions
- `writeup.md` - writeup template

## Main Features

- FastAPI backend with typed Pydantic schemas
- SQLite persistence for notes and action items
- Frontend served directly by FastAPI at `/`
- Action item extraction from free-form text
- Ollama-based LLM extraction with structured JSON output
- Save note while extracting via `save_note`
- Mark action items done/undone
- List notes and action items

## Requirements

- Python 3.10+
- Poetry
- Ollama installed and running locally
- Ollama model pulled (default: `llama3.2`)

Dependencies are defined in the root `pyproject.toml`.

## Setup

Run from repository root:

1. Create and activate environment (example with conda)

```bash
conda create -n cs146s python=3.12 -y
conda activate cs146s
```

2. Install dependencies

```bash
poetry install
```

3. Pull Ollama model used by default

```bash
ollama pull llama3.2
```

Optional environment variables used by extractor:

- `OLLAMA_MODEL` (default: `llama3.2`)
- `OLLAMA_TEMPERATURE` (default: `0`)

## Run the App

From repository root:

```bash
poetry run uvicorn week2.app.main:app --reload
```

Open:

- App UI: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

On startup, DB tables are created automatically in `week2/data/app.db`.

## Frontend Behavior

The page at `/` includes:

- `Extract` button -> calls `/action-items/extract`
- `Extract LLM` button -> calls `/action-items/extract-llm`
- `List Notes` button -> calls `GET /notes`
- checkbox toggle per action item -> calls `POST /action-items/{id}/done`

## API Endpoints

### `GET /`

Serve frontend HTML page.

### `POST /notes`

Create a note.

Request:

```json
{
  "content": "Prepare demo and send follow-up email."
}
```

Response (`201`):

```json
{
  "id": 1,
  "content": "Prepare demo and send follow-up email.",
  "created_at": "2026-03-11 10:00:00"
}
```

### `GET /notes`

List all notes (newest first).

### `GET /notes/{note_id}`

Get one note by ID.

- Returns `404` if note is not found.

### `POST /action-items/extract`

Extract action items from text, optionally save note.

Request:

```json
{
  "text": "TODO: follow up with vendor. Action: draft rollout email.",
  "save_note": true
}
```

Response:

```json
{
  "note_id": 1,
  "items": [
    { "id": 1, "text": "Follow up with vendor" },
    { "id": 2, "text": "Draft rollout email" }
  ]
}
```

### `POST /action-items/extract-llm`

Same request/response schema as `/action-items/extract`, but through the explicit LLM route.

### `GET /action-items`

List action items.

Optional query param:

- `note_id` -> filter by note

Example:

```text
GET /action-items?note_id=1
```

### `POST /action-items/{action_item_id}/done`

Mark or unmark action item.

Request:

```json
{
  "done": true
}
```

Response:

```json
{
  "id": 1,
  "done": true
}
```

- Returns `404` if action item is not found.

## Run Tests

From repository root:

```bash
python -m pytest week2/tests -v
```

or explicitly with conda interpreter:

```bash
C:/Users/USER/.conda/envs/cs146s/python.exe -m pytest week2/tests -v
```

Current tests in `week2/tests/test_extract.py` cover:

- bullet-list input
- keyword-prefixed input
- empty input
- delegation from `extract_action_items()` to `extract_action_items_llm()`

## Notes

- Frontend is intentionally minimal (single HTML file).
- DB access uses `sqlite3` directly.
- Request/response contracts are in `app/schemas.py`.
- Extraction endpoints depend on Ollama availability and model readiness.
