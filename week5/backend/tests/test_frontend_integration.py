def _create_note(client, title: str, content: str) -> dict:
    response = client.post("/notes/", json={"title": title, "content": content})
    assert response.status_code == 201, response.text
    return response.json()


def _create_action_item(client, description: str) -> dict:
    response = client.post("/action-items/", json={"description": description})
    assert response.status_code == 201, response.text
    return response.json()


def test_frontend_shell_serves_expected_dom_hooks(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert 'id="note-form"' in html
    assert 'id="action-form"' in html
    assert '<script src="/static/app.js"></script>' in html


def test_frontend_search_flow_via_notes_search_endpoint(client):
    matching = _create_note(client, title="frontend-search-match", content="alpha")
    _create_note(client, title="frontend-search-other", content="beta")

    response = client.get("/notes/search/", params={"q": "match"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == matching["id"]


def test_frontend_pagination_flow_via_notes_list_endpoint(client):
    for idx in range(5):
        _create_note(client, title=f"title-{idx}", content=f"content-{idx}")

    first_page = client.get("/notes/", params={"page": 1, "page_size": 2})
    assert first_page.status_code == 200
    first_data = first_page.json()
    assert first_data["total"] == 5
    assert len(first_data["items"]) == 2
    assert [item["title"] for item in first_data["items"]] == ["title-0", "title-1"]

    third_page = client.get("/notes/", params={"page": 3, "page_size": 2})
    assert third_page.status_code == 200
    third_data = third_page.json()
    assert third_data["total"] == 5
    assert len(third_data["items"]) == 1
    assert third_data["items"][0]["title"] == "title-4"


def test_frontend_optimistic_complete_retry_pattern_is_safe(client):
    item = _create_action_item(client, description="optimistic-retry")
    item_id = item["id"]

    first = client.put(f"/action-items/{item_id}/complete")
    assert first.status_code == 200
    assert first.json()["completed"] is True

    retry = client.put(f"/action-items/{item_id}/complete")
    assert retry.status_code == 200
    assert retry.json()["completed"] is True

    items = client.get("/action-items/")
    assert items.status_code == 200
    payload = items.json()
    assert len(payload) == 1
    assert payload[0]["id"] == item_id
    assert payload[0]["completed"] is True
