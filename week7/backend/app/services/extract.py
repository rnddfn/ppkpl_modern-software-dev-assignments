import re

TASK_BULLET_RE = re.compile(r"^(?:[-*]|\d+[.)])\s+")
CHECKBOX_RE = re.compile(r"^\[(?:\s|x|X)\]\s+")
PREFIX_RE = re.compile(r"^(?:todo|action|next\s*step|follow\s*up|fixme|task)\s*:\s*", re.IGNORECASE)
ACTION_VERB_RE = re.compile(
    r"^(?:add|analyze|build|check|clean|confirm|create|deploy|document|draft|fix|implement|"
    r"investigate|prepare|refactor|remove|review|schedule|send|ship|test|update|write)\b",
    re.IGNORECASE,
)
ASSIGNMENT_RE = re.compile(
    r"\b(?:i|we|you|[A-Z][a-z]+)\s+to\s+(?:add|build|check|create|deploy|fix|review|"
    r"send|test|update|write|prepare|schedule|investigate|implement)\b"
)
DEADLINE_RE = re.compile(
    r"\b(?:by|before|due)\s+(?:eod|tomorrow|today|next\s+week|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)


def _clean_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = TASK_BULLET_RE.sub("", cleaned)
    cleaned = CHECKBOX_RE.sub("", cleaned)
    return cleaned.strip()


def _is_actionable(line: str) -> bool:
    if not line or line.endswith("?"):
        return False

    normalized = line.lower()
    if normalized.startswith("todo:") or normalized.startswith("action:"):
        return True
    if PREFIX_RE.match(line):
        return True
    if ACTION_VERB_RE.match(line):
        return True
    if ASSIGNMENT_RE.search(line):
        return True
    if DEADLINE_RE.search(line):
        return True
    if normalized in {"ship it!", "do it!"}:
        return True
    return False


def extract_action_items(text: str) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not _is_actionable(line):
            continue

        key = line.casefold()
        if key in seen:
            continue

        seen.add(key)
        results.append(line)

    return results


