import pytest


def _create_note(client, title: str = "Test", content: str = "Hello world") -> dict:
    response = client.post("/notes/", json={"title": title, "content": content})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_list_notes(client):
    created = _create_note(client)
    assert created["title"] == "Test"
    assert created["content"] == "Hello world"

    response = client.get("/notes/")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"items", "total"}
    assert payload["total"] >= 1
    assert any(item["id"] == created["id"] for item in payload["items"])

    response = client.get("/notes/search/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    response = client.get("/notes/search/", params={"q": "Hello"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert any(item["id"] == created["id"] for item in items)


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "Missing content"},
        {"content": "Missing title"},
        {},
    ],
)
def test_create_note_rejects_invalid_payload(client, payload):
    response = client.post("/notes/", json=payload)
    assert response.status_code in {400, 422}


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": -1},
        {"page_size": 0},
        {"page_size": 101},
    ],
)
def test_list_notes_rejects_invalid_pagination_parameters(client, params):
    response = client.get("/notes/", params=params)
    assert response.status_code in {400, 422}


def test_get_note_returns_404_for_unknown_id(client):
    response = client.get("/notes/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_get_note_rejects_non_integer_id(client):
    response = client.get("/notes/not-an-int")
    assert response.status_code in {400, 422}


def test_search_notes_filters_expected_records(client):
    expected = _create_note(client, title="alpha-title", content="alpha-content")
    _create_note(client, title="beta-title", content="beta-content")

    response = client.get("/notes/search/", params={"q": "alpha-title"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["id"] == expected["id"]
