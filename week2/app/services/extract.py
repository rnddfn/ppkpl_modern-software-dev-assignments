from __future__ import annotations

import os
from typing import List

from ollama import chat
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
DEFAULT_OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0"))


class ActionItemsResponse(BaseModel):
    items: List[str] = Field(default_factory=list)


SYSTEM_PROMPT = """Extract only actionable tasks from the user's notes.
Return JSON that matches the provided schema.
Rules:
- Include only concrete tasks someone can do.
- Rewrite each task as a concise standalone action item.
- Exclude context, status updates, and non-actionable discussion.
- Preserve the original meaning.
- Return an empty list when there are no action items.
"""


def _normalize_action_items(items: List[str]) -> List[str]:
    seen: set[str] = set()
    normalized: List[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(cleaned)
    return normalized


def _read_message_content(response: object) -> str:
    message = getattr(response, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content

    if isinstance(response, dict):
        message_payload = response.get("message", {})
        content = message_payload.get("content", "")
        if isinstance(content, str):
            return content

    raise ValueError("Ollama returned a response without JSON content")


def extract_action_items_llm(text: str, model: str | None = None) -> List[str]:
    content = text.strip()
    if not content:
        return []

    response = chat(
        model=model or DEFAULT_OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        format=ActionItemsResponse.model_json_schema(),
        options={"temperature": DEFAULT_OLLAMA_TEMPERATURE},
    )

    try:
        parsed = ActionItemsResponse.model_validate_json(_read_message_content(response))
    except ValidationError as exc:
        raise ValueError("Ollama returned an invalid action item payload") from exc

    return _normalize_action_items(parsed.items)


def extract_action_items(text: str) -> List[str]:
    return extract_action_items_llm(text)
