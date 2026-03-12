from backend.app.services.extract import extract_action_items


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - ACTION: review PR
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "ACTION: review PR" in items
    assert "Ship it!" in items


def test_extract_action_items_with_checkboxes_and_numbered_lines():
    text = """
    [ ] Update deployment docs
    1. Refactor parser for better errors
    * [x] Deploy to staging
    We had a meeting yesterday.
    """.strip()

    items = extract_action_items(text)

    assert "Update deployment docs" in items
    assert "Refactor parser for better errors" in items
    assert "Deploy to staging" in items
    assert "We had a meeting yesterday." not in items


def test_extract_action_items_with_assignment_and_deadline_patterns():
    text = """
    Alice to review onboarding PR by Friday
    Prepare release notes before 2026-03-20
    This looks good overall.
    Can you check this?
    """.strip()

    items = extract_action_items(text)

    assert "Alice to review onboarding PR by Friday" in items
    assert "Prepare release notes before 2026-03-20" in items
    assert "This looks good overall." not in items
    assert "Can you check this?" not in items


def test_extract_action_items_removes_duplicates_case_insensitive():
    text = """
    TODO: write tests
    todo: write tests
    - [ ] Write tests
    """.strip()

    items = extract_action_items(text)
    assert items == ["TODO: write tests", "Write tests"]


