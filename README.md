# Action Item Extractor

This repository contains several course assignments, but the runnable application in the current codebase is the Week 2 Action Item Extractor.

It is a small FastAPI + SQLite app that lets you:

- paste free-form notes into a browser
- extract action items from those notes
- optionally save the original note
- store extracted action items in SQLite
- mark action items as done
- list saved notes

The app also includes an Ollama-powered extraction flow. The frontend exposes both `Extract` and `Extract LLM` buttons, and both flows currently depend on the extraction service in `week2/app/services/extract.py`.

## Project Structure

- `week2/app/main.py`: FastAPI application entry point
- `week2/app/routers/notes.py`: note creation and note listing endpoints
- `week2/app/routers/action_items.py`: extraction, action item listing, and mark-done endpoints
- `week2/app/services/extract.py`: action item extraction logic using Ollama structured output
- `week2/app/db.py`: SQLite setup and database helper functions
- `week2/frontend/index.html`: minimal HTML frontend
- `week2/tests/test_extract.py`: unit tests for extraction behavior

## Main Features

- FastAPI backend with typed Pydantic request and response schemas
- SQLite persistence for notes and action items
- Browser UI served directly by FastAPI at `/`
- Action item extraction from note text
- Ollama-based LLM extraction with structured JSON output
- Ability to save notes while extracting
- Ability to mark saved action items as done
- API docs available through FastAPI's built-in Swagger UI

## Requirements

- Python 3.10+
- Poetry
- Ollama installed locally if you want extraction to work

Python dependencies are defined in `pyproject.toml`.

## Local Setup

From the repository root:

1. Create and activate a Python environment.

```bash
conda create -n cs146s python=3.12 -y
conda activate cs146s
```

2. Install Poetry if it is not already installed.

```bash
curl -sSL https://install.python-poetry.org | python -
```

3. Install project dependencies.

```bash
poetry install
```

4. Install and start Ollama.

Pull the default model used by the app:

```bash
ollama pull llama3.2
```

If you want to use a different model, set `OLLAMA_MODEL` before starting the app.

Optional environment variables:

- `OLLAMA_MODEL`: model name used by the extractor, defaults to `llama3.2`
- `OLLAMA_TEMPERATURE`: generation temperature, defaults to `0`

## Running the App

Start the FastAPI server from the repository root:

```bash
poetry run uvicorn week2.app.main:app --reload
```

Then open:

- App UI: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

When the app starts, it automatically creates the SQLite database in `week2/data/app.db` if it does not already exist.

## How the App Works

1. You paste notes into the textarea in the frontend.
2. The frontend sends the note text to one of the extraction endpoints.
3. The backend extracts action items and optionally saves the note.
4. Extracted action items are inserted into the SQLite database.
5. The frontend renders the saved action items and lets you mark them as done.
6. The `List Notes` button calls `GET /notes` and shows previously saved notes.

## API Endpoints

### `GET /`

Serves the minimal HTML frontend.

### `POST /notes`

Create a note.

Request body:

```json
{
   "content": "Schedule a demo and update the onboarding guide."
}
```

Response:

```json
{
   "id": 1,
   "content": "Schedule a demo and update the onboarding guide.",
   "created_at": "2026-03-11 10:00:00"
}
```

### `GET /notes`

Return all saved notes in reverse creation order.

### `GET /notes/{note_id}`

Return one note by ID.

- Returns `404` if the note does not exist.

### `POST /action-items/extract`

Extract action items from note text and optionally save the note.

Request body:

```json
{
   "text": "TODO: follow up with the vendor. Action: draft the rollout email.",
   "save_note": true
}
```

Response:

```json
{
   "note_id": 1,
   "items": [
      {"id": 1, "text": "Follow up with the vendor"},
      {"id": 2, "text": "Draft the rollout email"}
   ]
}
```

Note: in the current code, `extract_action_items()` delegates to the Ollama-backed extractor, so this route also depends on Ollama being available.

### `POST /action-items/extract-llm`

Extract action items using the explicit Ollama LLM path.

This endpoint accepts the same request body and returns the same response shape as `/action-items/extract`.

### `GET /action-items`

List all saved action items.

Optional query parameter:

- `note_id`: filter action items by note

Example:

```text
GET /action-items?note_id=1
```

### `POST /action-items/{action_item_id}/done`

Mark an action item as done or not done.

Request body:

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

- Returns `404` if the action item does not exist.

## Running Tests

Run the Week 2 test suite from the repository root:

```bash
python -m pytest week2/tests -v
```

Or with the course Conda environment explicitly:

```bash
C:/Users/USER/.conda/envs/cs146s/python.exe -m pytest week2/tests -v
```

Current tests cover the extraction service in `week2/tests/test_extract.py`, including:

- bullet-list inputs
- keyword-prefixed inputs
- empty input
- delegation from `extract_action_items()` to the LLM extractor

## Notes for Development

- The frontend is intentionally simple and lives in a single HTML file.
- The database layer uses `sqlite3` directly rather than an ORM.
- FastAPI request and response schemas are defined in `week2/app/schemas.py`.
- If Ollama is not running or the configured model is missing, extraction requests will fail.