from types import SimpleNamespace

from ..app.services.extract import extract_action_items, extract_action_items_llm


def _fake_response(payload: str) -> SimpleNamespace:
    return SimpleNamespace(message=SimpleNamespace(content=payload))


def test_extract_action_items_llm_from_bullet_notes(monkeypatch):
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    def fake_chat(**kwargs):
        assert kwargs["messages"][1]["content"] == text
        return _fake_response(
            '{"items": ["Set up database", "Implement API extract endpoint", "Write tests"]}'
        )

    monkeypatch.setattr("week2.app.services.extract.chat", fake_chat)

    items = extract_action_items_llm(text)

    assert items == [
        "Set up database",
        "Implement API extract endpoint",
        "Write tests",
    ]


def test_extract_action_items_llm_from_keyword_prefixed_lines(monkeypatch):
    text = """
    TODO: follow up with the vendor
    Action: draft the rollout email
    Next: prepare a demo for Friday
    """.strip()

    monkeypatch.setattr(
        "week2.app.services.extract.chat",
        lambda **kwargs: _fake_response(
            '{"items": ["Follow up with the vendor", "Draft the rollout email", "Prepare a demo for Friday"]}'
        ),
    )

    items = extract_action_items_llm(text)

    assert items == [
        "Follow up with the vendor",
        "Draft the rollout email",
        "Prepare a demo for Friday",
    ]


def test_extract_action_items_llm_returns_empty_for_empty_input(monkeypatch):
    def fake_chat(**kwargs):
        raise AssertionError("chat should not be called for empty input")

    monkeypatch.setattr("week2.app.services.extract.chat", fake_chat)

    assert extract_action_items_llm("   \n\t  ") == []


def test_extract_action_items_delegates_to_llm(monkeypatch):
    monkeypatch.setattr(
        "week2.app.services.extract.extract_action_items_llm",
        lambda text: ["Create release checklist"],
    )

    assert extract_action_items("Ship prep notes") == ["Create release checklist"]
